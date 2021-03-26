        
    # def draw_conflicts_graph(self, tabIdx):
    #     if tabIdx == 2:    
    #         self.ui.conflicts_graph.model().clear()
    #         mods = self.profile_handler.get_active_mods()
    #         graph = generate_patched_mods(mods, self.output_loc)  
    #         graph = prepare_graph_for_display(graph)
    #         self.ui.conflicts_graph.setAlternatingRowColors(True)
    #         header_labels = ["File", *[mod.name for mod in mods], "Used Mod"]
    #         self.ui.conflicts_graph.model().setHorizontalHeaderLabels(header_labels)
    #         self.draw_conflicts_subgraph(graph, mods)
                
    # def draw_conflicts_subgraph(self, graph, mods, parent=None):
    #     colours = {0: QtGui.QColor( 150,  150,  150),
    #        1: QtGui.QColor(  0,   0,   0),
    #        2: QtGui.QColor(255, 255,   0),
    #        3: QtGui.QColor(  0,   0, 255),
    #        4: QtGui.QColor(255,   0,   0),
    #        5: QtGui.QColor(200, 255, 200),
    #        6: QtGui.QColor(  0, 255,   0),
    #        7: QtGui.QColor(  0, 255, 255)}
        
    #     if parent is None:
    #         parent = self.ui.conflicts_graph.model().invisibleRootItem()
        
    #     for j, (key, value) in enumerate(graph.items()):
    #         nameitem = QtGui.QStandardItem(key)
    #         modelitem = [nameitem, *[QtGui.QStandardItem() for _ in mods], QtGui.QStandardItem()]
    #         for i in range(len(mods)):
    #             if type(value) != dict:
    #                 modelitem[i+1].setData(colours[value[i]], QtCore.Qt.BackgroundRole)
    #             #else:
    #             #    modelitem[i+1].setData(colours[0], QtCore.Qt.BackgroundRole)
    #         for item in modelitem:                
    #             item.setEditable(False)
    #         parent.appendRow(modelitem)
    #         if type(value) == dict:
    #             self.draw_conflicts_subgraph(value, mods, nameitem)
            
    
    # def prepare_graph_for_display(graph):
#     directories = {}
#     files = {}
#     for key in sorted(graph):
#         keysplit = key.split('/')
#         value = graph[key]
#         if len(keysplit) > 1:
#             if keysplit[0] not in directories:
#                 directories[keysplit[0]] = {}
#             directories[keysplit[0]]['/'.join(keysplit[1:])] = value
#         else:
#             files[key] = value
            
#     for key, value in directories.items():
#         directories[key] = prepare_graph_for_display(value)
            
#     return {**directories, **files}
