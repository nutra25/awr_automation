import pyawr.mwoffice as mwoffice
from collections import deque


def get_element_data(app_instance, schematic_name, target_name):
    """Reads the center (x, y) coordinates and node coordinates of the specified element."""
    try:
        schematic = app_instance.Project.Schematics(schematic_name)
    except Exception:
        print(f"[AWR_Automation] |-- [Schematic] |-- ERROR: Schematic '{schematic_name}' not found.")
        return None, None, []

    target_element = None
    for elem in schematic.Elements:
        if elem.Name == target_name or (
                elem.Parameters.Exists("ID") and elem.Parameters("ID").ValueAsString == target_name):
            target_element = elem
            break

    if not target_element:
        print(f"[AWR_Automation] |-- [Element] |-- ERROR: Element '{target_name}' not found.")
        return None, None, []

    center_x = target_element.x
    center_y = target_element.y

    node_coords = []
    for node in target_element.Nodes:
        node_coords.append((node.x, node.y))

    print(
        f"[AWR_Automation] |-- [Element] |-- INFO: Read data for [{target_name}]. Center: ({center_x}, {center_y}), Nodes: {len(node_coords)}")
    return center_x, center_y, node_coords


def delete_element(app_instance, schematic_name, target_name):
    """Deletes the specified element from the schematic."""
    schematic = app_instance.Project.Schematics(schematic_name)

    target_element = None
    for elem in schematic.Elements:
        if elem.Name == target_name or (
                elem.Parameters.Exists("ID") and elem.Parameters("ID").ValueAsString == target_name):
            target_element = elem
            break

    if target_element:
        old_name = target_element.Name
        target_element.Delete()
        print(f"[AWR_Automation] |-- [Element] |-- SUCCESS: Deleted [{old_name}].")
        return True
    else:
        print(f"[AWR_Automation] |-- [Element] |-- WARNING: Element to delete ({target_name}) not found.")
        return False


def add_new_library_element(app_instance, schematic_name, browser_path, x_pos, y_pos):
    """Adds a new element from the library to the specified coordinates and returns its name."""
    schematic = app_instance.Project.Schematics(schematic_name)

    try:
        new_element = schematic.Elements.AddLibraryElement(browser_path, x_pos, y_pos)
        print(f"[AWR_Automation] |-- [Library] |-- SUCCESS: Added library element. Assigned Name: {new_element.Name}")
        return new_element.Name
    except Exception as e:
        print(f"[AWR_Automation] |-- [Library] |-- ERROR: Failed to add library element. Details: {e}")
        return None


def rewire_mapped_element(app_instance, schematic_name, new_element_name, old_node_coords, node_mapping):
    """
    Draws wires between the old node coordinates and the new element's nodes based on a specific mapping.

    :param node_mapping: dict, e.g., {7: 1, 2: 2} -> Maps old node index (key) to new node index (value).
                         Note: AWR node indices are typically 1-based, but Python lists are 0-based.
    """
    schematic = app_instance.Project.Schematics(schematic_name)

    if not schematic.Elements.Exists(new_element_name):
        print(f"[AWR_Automation] |-- [Wiring] |-- ERROR: Target element '{new_element_name}' not found for wiring.")
        return

    new_element = schematic.Elements(new_element_name)

    # Store new node coordinates
    new_node_coords = []
    for node in new_element.Nodes:
        new_node_coords.append((node.x, node.y))

    wire_count = 0
    print(f"[AWR_Automation] |-- [Wiring] |-- INFO: Starting targeted wiring process for {new_element_name}.")

    for old_node_idx, new_node_idx in node_mapping.items():
        # Convert 1-based schematic node index to 0-based Python list index
        old_list_idx = old_node_idx - 1
        new_list_idx = new_node_idx - 1

        # Validate indices to prevent IndexError
        if old_list_idx >= len(old_node_coords):
            print(
                f"[AWR_Automation] |-- [Wiring] |-- WARNING: Old node index {old_node_idx} is out of bounds. Skipping.")
            continue
        if new_list_idx >= len(new_node_coords):
            print(
                f"[AWR_Automation] |-- [Wiring] |-- WARNING: New node index {new_node_idx} is out of bounds. Skipping.")
            continue

        old_x, old_y = old_node_coords[old_list_idx]
        new_x, new_y = new_node_coords[new_list_idx]

        # Draw wire if there is a gap between coordinates
        if old_x != new_x or old_y != new_y:
            schematic.Wires.Add(old_x, old_y, new_x, new_y)
            wire_count += 1
            print(
                f"[AWR_Automation] |-- [Wiring] |-- SUCCESS: Wired Old Node {old_node_idx} -> New Node {new_node_idx} | Coords: ({old_x}, {old_y}) -> ({new_x}, {new_y})")
        else:
            print(
                f"[AWR_Automation] |-- [Wiring] |-- INFO: Nodes {old_node_idx} and {new_node_idx} perfectly overlap. No wire needed.")

    print(f"[AWR_Automation] |-- [Wiring] |-- SUMMARY: Completed with {wire_count} physical wire connections.")


if __name__ == "__main__":
    app = mwoffice.CMWOffice()
    schematic_name = "Load_Pull_Template"
    target_element = "CFH1"
    library_path = "BP:\\Circuit Elements\\Libraries\\*MA_RFP -- v0.0.2.5\\GaN Product\\CGHV1F006S"

    # Define the custom pin mapping (1-based index)
    # Format: {Old_Element_Node: New_Element_Node}
    custom_node_mapping = {
        1: 1,  # Old node 1 connects to New node 1
        2: 2,  # Old node 2 connects to New node 2
        7: 1  # Old node 7 connects to New node 1
    }

    print(f"[AWR_Automation] |-- [Main] |-- INFO: Initiating element replacement protocol.")

    # 1. Read Data
    cx, cy, old_nodes = get_element_data(app, schematic_name, target_element)

    if old_nodes:
        # 2. Delete Old Element
        delete_element(app, schematic_name, target_element)

        # 3. Add New Element from Library
        new_name = add_new_library_element(app, schematic_name, library_path, cx, cy)

        # 4. Wire the specific mapped nodes
        if new_name:
            rewire_mapped_element(app, schematic_name, new_name, old_nodes, custom_node_mapping)