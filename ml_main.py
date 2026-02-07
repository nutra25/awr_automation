import optuna
from optuna.samplers import NSGAIISampler  # Çok amaçlı optimizasyonun kralı
from main import SimulationManager
import logging

# Log kalabalığını önleyelim
optuna.logging.set_verbosity(optuna.logging.WARNING)


class MultiObjectiveOptimizer:
    def __init__(self):
        self.sim_engine = SimulationManager()

        # Kesin Gereksinimler (Hard Constraints)
        self.MIN_PLOAD = 37.8
        self.MIN_PAE = 49.0

        # Arama Aralıkları
        self.RANGES = {
            "P_in": {"min": 25.0, "max": 32.0},
            "VGS": {"min": -3.0, "max": -1.5}
        }

    def objective(self, trial):
        """
        AI bu fonksiyonu her çalıştırdığında iki değer döndürecek: (Pload, PAE).
        Böylece aralarındaki ilişkiyi (Trade-off) haritalandıracak.
        """

        # 1. PARAMETRE SEÇİMİ (AI Öneriyor)
        freq = 13.1  # Sabit
        p_in = trial.suggest_float("P_in", self.RANGES["P_in"]["min"], self.RANGES["P_in"]["max"])
        vgs = trial.suggest_float("VGS", self.RANGES["VGS"]["min"], self.RANGES["VGS"]["max"])

        state_tuple = (freq, p_in, vgs)

        print(f"\n[AI] Deneme #{trial.number}: {state_tuple} analiz ediliyor...")

        # 2. SİMÜLASYON (Black Box)
        try:
            # Sizin kodunuz çalışıyor
            results = self.sim_engine.run_state(state_tuple, state_idx=trial.number, total_states=50)

            # Sonuçları al
            pload = float(results.get("PLoad [dBm]", -1))
            pae = float(results.get("PAE [%]", -1))

        except Exception as e:
            print(f"[Hata] Simülasyon başarısız: {e}")
            # Hata durumunda çok kötü iki değer döndür ki AI burayı seçmesin
            return -1.0, -1.0

        print(f"     -> Sonuç: Pload={pload:.2f} dBm, PAE={pae:.2f}%")

        # 3. İKİ HEDEFİ DE DÖNDÜR (Puanlama Yok, Ham Veri Var)
        # AI artık "Puanım kaç?" demiyor. "Gücüm şu, Verimim bu" diyor.
        # Trade-off'u kendi algoritmasıyla (NSGA-II) çözecek.
        return pload, pae

    def run(self, n_trials=50):
        print("--- Çok Amaçlı (Pareto) Optimizasyon Başlıyor ---")

        # ÖNEMLİ KISIM:
        # directions=["maximize", "maximize"] -> Hem Pload hem PAE artsın istiyoruz.
        # sampler=NSGAIISampler() -> Genetik algoritma ile en iyi nesilleri türetir.
        study = optuna.create_study(
            directions=["maximize", "maximize"],
            sampler=NSGAIISampler()
        )

        study.optimize(self.objective, n_trials=n_trials)

        print("\n--- Optimizasyon Bitti: En İyi Adaylar Seçiliyor ---")

        # Optuna bize "Pareto Cephesi"ndeki (En iyi trade-off noktaları) denemeleri verir
        best_trials = study.best_trials

        valid_solutions = []

        print(f"\nBulunan {len(best_trials)} adet Pareto Çözümü arasından filtreleme yapılıyor:")
        print(f"Hedef: Pload > {self.MIN_PLOAD} dBm VE PAE > {self.MIN_PAE}%")
        print("-" * 60)

        for trial in best_trials:
            val_pload = trial.values[0]
            val_pae = trial.values[1]
            params = trial.params

            # Sizin Şartlarınızı Kontrol Ediyoruz
            if val_pload >= self.MIN_PLOAD and val_pae >= self.MIN_PAE:
                print(f"[UYGUN] Pload: {val_pload:.2f} | PAE: {val_pae:.2f}% | Parametreler: {params}")
                valid_solutions.append((val_pload, val_pae, params))
            else:
                print(f"[Yetersiz] Pload: {val_pload:.2f} | PAE: {val_pae:.2f}% (Elendi)")

        if valid_solutions:
            # En uygunlar arasından PAE'si en yüksek olanı "Kazanan" ilan edelim
            winner = max(valid_solutions, key=lambda x: x[1])  # x[1] = PAE
            print("\n" + "=" * 40)
            print(f" KAZANAN PARAMETRELER (Max PAE)")
            print("=" * 40)
            print(f"P_in : {winner[2]['P_in']:.4f} dBm")
            print(f"VGS  : {winner[2]['VGS']:.4f} V")
            print(f"Sonuç: Pload={winner[0]:.2f} dBm, PAE={winner[1]:.2f}%")
        else:
            print("\nMaalesef tam kriterlere uyan bir nokta bulunamadı.")
            print("Pareto eğrisindeki en yakın sonuçlara bakarak hedefleri gevşetmeyi düşünün.")


if __name__ == "__main__":
    optimizer = MultiObjectiveOptimizer()
    optimizer.run(n_trials=40)