# rv_node_graph_qt.py

"""
RV Node Graph Visualization using PySide2 and NodeGraphQt.
"""

# Third-party imports
from PySide2 import QtWidgets, QtCore, QtGui
import NodeGraphQt
import NodeGraphQt.constants as ngqt_constants

# RV-specific imports
import rv.commands as rvc
import rv.rvtypes


# --- NodeGraphQt Custom Nodes ---
class RVNode(NodeGraphQt.BaseNode):
    """
    A custom NodeGraphQt node to represent a standard (non-group) node
    in the RV graph. Input ports are added dynamically.
    """
    __identifier__ = 'rv'
    NODE_NAME = 'RVNode'  # Default, will be overridden

    def __init__(self):
        super(RVNode, self).__init__()
        # Output port - assuming one primary output for simplicity.
        self.add_input("in", multi_input=True, color=(180, 80, 0))
        self.add_output('out', color=(0, 102, 153))
        self.create_property('original_name', '', widget_type=ngqt_constants.NodePropWidgetEnum.QLABEL.value)
        self.create_property('node_type', '', widget_type=ngqt_constants.NodePropWidgetEnum.QLABEL.value)


class RVGroupNode(NodeGraphQt.GroupNode):
    """
    A custom NodeGraphQt node to represent a group node in the RV graph.
    This class is primarily for visual grouping.
    """
    __identifier__ = 'rv'
    NODE_NAME = 'RVGroup'  # Default, will be overridden

    def __init__(self):
        super(RVGroupNode, self).__init__()
        # Output port - assuming one primary output for simplicity.
        self.add_input("in", multi_input=True, color=(180, 80, 0))
        self.add_output('out', color=(0, 102, 153))
        self.create_property('original_name', '', widget_type=ngqt_constants.NodePropWidgetEnum.QLABEL.value)
        self.create_property('node_type', '', widget_type=ngqt_constants.NodePropWidgetEnum.QLABEL.value)

    def expand(self):
        """Expands the group node to show its contents."""
        was_expanded = self.is_expanded
        sub_graph = super(RVGroupNode, self).expand()
        if not was_expanded:
            # Connect signals to the subgraph
            sub_graph.node_selection_changed.connect(_on_node_selection_changed)
            sub_graph.node_double_clicked.connect(_on_node_double_clicked)
            # Make the menus
            sub_graph.get_context_menu('nodes').add_command('Expand Group',
                                                            func=expand_group_node,
                                                            node_type='rv.RVGroupNode')
        return sub_graph


# --- Helper Functions ---

def get_node_color(node_type):
    """Returns a QColor tuple (r, g, b) based on the RV node type string."""
    if not node_type:
        return 100, 100, 100
    if "Source" in node_type:
        return 80, 120, 80
    if "LUT" in node_type:
        return 150, 120, 80
    if "Filter" in node_type:
        return 120, 100, 80
    if "View" in node_type or "Display" in node_type:
        return 80, 80, 130
    if "Sequence" in node_type:
        return 130, 80, 130
    if "Stack" in node_type:
        return 80, 130, 130
    if "Layout" in node_type:
        return 130, 130, 80
    if "Group" in node_type:
        return 110, 110, 110  # Fallback for other groups
    return 100, 100, 100


def get_rv_hierarchy():
    """
    Returns a dictionary representing the RV node hierarchy.

    Note
    ----
    RV nodes command will always return a parent before a child.

    Returns
    -------
    dict[str, dict]
    """
    root_nodes = {}
    all_nodes_map = {}
    for node_name in rvc.nodes():
        group = rvc.nodeGroup(node_name)
        if not group:
            root_nodes[node_name] = {}
            all_nodes_map[node_name] = root_nodes[node_name]
        else:
            parent_group = all_nodes_map[group]
            parent_group[node_name] = {}
            all_nodes_map[node_name] = parent_group[node_name]
    return root_nodes


def expand_group_node(graph, node):
    """
    Expands a group node in the NodeGraphQt graph.
    """
    if not node.is_expanded:
        node.expand()
        print(f"Expanding group node: {node.name()}")


def _on_node_selection_changed(selected_nodes, deselected_nodes):
    if selected_nodes:
        for node in selected_nodes:
            # Get RV name and node type
            node_name = node.get_property('original_name')
            node_type = node.get_property('node_type')
            properties = rvc.properties(node_name)
            print(f"INFO: #### {node_name} ({node_type})####\n{properties}")
    #     node_names = [n.name() for n in selected_nodes]
    #     print(f"Nodes selected: {', '.join(node_names)}")
    # if deselected_nodes:
    #     node_names = [n.name() for n in deselected_nodes]
    #     print(f"Nodes deselected: {', '.join(node_names)}")


def _on_node_double_clicked(node):
    print(f"Node double-clicked: {node.name()} (Type: {node.type_})")
    if isinstance(node, RVGroupNode):
        expand_group_node(node.graph, node)


# --- Main Dialog Class ---
class RVNodeGraphDialog(QtWidgets.QMainWindow):
    """
    A custom dialog class for displaying the RV node graph.
    This class is primarily for visual grouping and does not add input ports.
    """

    def __init__(self, parent=None):
        super(RVNodeGraphDialog, self).__init__(parent)
        self.setWindowTitle("RV Node Graph Inspector")
        self.setMinimumSize(800, 500)
        self.resize(1200, 800)
        self._node_graph = self._init_graph()
        # self.properties_bin = NodeGraphQt.PropertiesBinWidget(parent=None, node_graph=self._node_graph)
        self.setCentralWidget(self._node_graph.widget)

    def _init_graph(self):
        """Initializes the NodeGraphQt instance."""
        graph = NodeGraphQt.NodeGraph()
        graph.set_background_color(45, 45, 45)
        graph.set_grid_color(60, 60, 60)
        graph.set_grid_mode(ngqt_constants.ViewerEnum.GRID_DISPLAY_DOTS)

        graph.node_selection_changed.connect(_on_node_selection_changed)
        graph.node_double_clicked.connect(_on_node_double_clicked)

        # Register nodes
        graph.register_node(RVNode)
        graph.register_node(RVGroupNode)

        # get the nodes menu.
        nodes_menu = graph.get_context_menu('nodes')
        # here we add override the context menu for "rv.group".
        nodes_menu.add_command('Expand Group',
                               func=expand_group_node,
                               node_type='rv.RVGroupNode')
        return graph

    # def show_bin(self, sel=None, desel=None):
    #     if not self.properties_bin.isVisible():
    #         print("Showing properties bin")
    #         self.properties_bin.show()
    #     for node in sel:
    #         self.properties_bin.add_node(node)

    def build_graph(self):
        """
        Builds the graph data and displays it in the NodeGraphQt window.
        This method should be called after initializing the graph.
        """
        # Clear existing nodes and connections
        self._node_graph.clear_session()

        def _stripped_name(node_name):
            """ Helper function to strip the parent group's name from the node name."""
            group = rvc.nodeGroup(node_name)
            if group and node_name.startswith(group):
                return node_name[len(group) + 1:]
            return node_name

        def _build_graph(graph, nodes):
            """ Function that builds the graph, or subgraph of a node"""
            print("Building graph with nodes:", nodes)
            for node_name in nodes:
                print(f"DEBUG: Adding node {node_name} to graph")
                node_type = rvc.nodeType(node_name)
                color = get_node_color(node_type)

                children = nodes[node_name]
                if children:
                    node = graph.create_node("rv.RVGroupNode")
                else:
                    node = graph.create_node("rv.RVNode")
                node.set_color(*color)
                node.set_name(_stripped_name(node_name))
                node.set_property('original_name', node_name)
                node.set_property('node_type', node_type)

            # Then we build the connections
            for node_name in nodes:
                node = graph.get_node_by_name(_stripped_name(node_name))
                if not node:
                    continue
                inputs, outputs = rvc.nodeConnections(node_name)
                print(f"DEBUG: Node {node_name} has inputs: {inputs}, outputs: {outputs}")
                if inputs:
                    print(f"INFO: Connecting inputs for node {node_name} with inputs: {inputs}")
                    in_port = node.input(0)
                    for input_node_name in inputs:
                        input_node = graph.get_node_by_name(_stripped_name(input_node_name))
                        if input_node:
                            input_node.output(0).connect_to(in_port)
                        else:
                            print(f"WARNING: Input node {input_node_name} not found for {node_name}")
                elif isinstance(graph, NodeGraphQt.SubGraph):
                    # If the node is a group node and has no inputs, we connect to the input port if there's one
                    input_ports = graph.get_input_port_nodes()
                    if input_ports:
                        input_port = input_ports[0]
                        in_port = node.input(0)
                        # We connect to the output port of the input port node
                        input_port.output(0).connect_to(in_port)
                if (not outputs or rvc.nodeGroup(outputs[0]) != rvc.nodeGroup(node_name)) and isinstance(graph,
                                                                                                         NodeGraphQt.SubGraph):
                    print(
                        f"INFO: Node {node_name}:{rvc.nodeType(node_name)} has no outputs, checking for group node connections.")
                    # If the node is a group node and has no outputs, we connect to the output port if there's one
                    output_ports = graph.get_output_port_nodes()
                    if output_ports:
                        output_port = output_ports[0]
                        out_port = node.output(0)
                        # We connect to the input port of the output port node
                        out_port.connect_to(output_port.input(0))

                # Now we need to populate the group nodes
                children = nodes[node_name]
                if children:
                    sub_graph = node.expand()
                    _build_graph(sub_graph, children)
                    node.collapse()

            # Then layout the graph
            graph.auto_layout_nodes()
            graph.fit_to_selection()
            graph.clear_selection()

        root_nodes = get_rv_hierarchy()
        _build_graph(self._node_graph, root_nodes)


# --- RV Minor Mode for Node Graph Visualization ---

class RVNodeGraphVizQt(rv.rvtypes.MinorMode):
    """
    RV Minor Mode to display the node graph using NodeGraphQt,
    handling dynamic inputs and group nodes.
    """

    def __init__(self):
        super(RVNodeGraphVizQt, self).__init__()
        self.init("rv_node_graph_viz_qt_v4",  # Mode name
                  [],  # Keyboard shortcuts
                  None,  # Event table
                  [("Node Graph", [("Inspect Node Graph", self.show_graph_window, None, None), ])])
        self.graph_dialog = None

    def show_graph_window(self, event=None):
        """
        Builds the graph data and displays it in a NodeGraphQt window.
        """
        # --- Create Dialog Window ---
        if not self.graph_dialog:
            self.graph_dialog = RVNodeGraphDialog()

        self.graph_dialog.build_graph()
        self.graph_dialog.show()
        self.graph_dialog.raise_()
        self.graph_dialog.activateWindow()


# --- RV Mode Loading Mechanism ---
g_the_mode = None


def createMode():
    global g_the_mode
    if g_the_mode is None:
        print("Creating RVNodeGraphVizQt mode instance.")
        g_the_mode = RVNodeGraphVizQt()
    return g_the_mode


def theMode():
    global g_the_mode
    if g_the_mode is None:
        createMode()
    return g_the_mode
