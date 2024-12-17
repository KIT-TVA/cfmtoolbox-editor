import networkx as nx
from typing import List, Tuple

class GraphDistanceCalculator:
    def __init__(self, G, root):
        self.G = G
        self.root = root
        self.pos = nx.random_layout(G)
        self.mod = {node: 0 for node in G.nodes}

    def compute_distances(self):
        self._set_initial_pos()
        self._compute_shift(self.root)
        self._compute_x(self.root)
        return self.pos

    def _set_initial_pos(self):
        bfs = list(nx.bfs_layers(self.G, self.root))
        for y in range(len(bfs)):
            for i in range(len(bfs[y])):
                name = bfs[y][i]
                self.pos[name][1] = -y

    def _compute_shift(self, node) -> Tuple[List[int], List[int]]:
        has_child, children = self._get_children(node)
        if not has_child:
            return [-len(node)], [len(node)]
        else:
            contours = {}
            for child in children:
                contours[child] = self._compute_shift(child)
            d = [0]
            for i in range(1, len(children)):
                d.append(0.5 * (len(children[i - 1]) + len(children[i])) + 10)
                sum_left = 0
                sum_right = 0
                for j in range(0, min(len(contours[children[i - 1]][1]), len(contours[children[i]][0]))):
                    sum_left += contours[children[i]][0][j]
                    sum_right += contours[children[i - 1]][1][j]
                    d[i] = max(d[i], sum_right - sum_left + 20)
            total_distance = sum(d)
            accumulated_distance = 0
            for i in range(len(children)):
                self.mod[children[i]] = accumulated_distance - total_distance / 2
                if (i + 1) < len(children):
                    accumulated_distance += d[i + 1]

            contour_left = [0]
            contour_left.append(self.mod[children[0]])
            old_contour = contours[children[0]][0]
            contour_left.extend(old_contour[1:])
            curr_height = len(contour_left)
            for i in range(1, len(children)):
                if len(contours[children[i]][0]) >= curr_height:
                    old_contour = contours[children[i]][0]
                    contour_left.append(sum(old_contour[0:curr_height]) + self.mod[children[i]] - self.mod[children[i - 1]] - sum(contours[children[i - 1]][0]))
                    contour_left.extend(old_contour[curr_height:len(old_contour)])
                    curr_height = len(contour_left)

            contour_right = [0]
            contour_right.append(self.mod[children[-1]])
            old_contour = contours[children[-1]][1]
            contour_right.extend(old_contour[1:])
            curr_height = len(contour_right)
            for i in range(len(children) - 2, -1, -1):
                if len(contours[children[i]][1]) >= curr_height:
                    old_contour = contours[children[i]][1]
                    contour_right.append(sum(old_contour[0:curr_height]) + self.mod[children[i]] - self.mod[children[i - 1]] - sum(contours[children[i - 1]][1]))
                    contour_right.extend(old_contour[curr_height:len(old_contour)])
                    curr_height = len(contour_right)

            return contour_left, contour_right

    def _compute_x(self, node):
        has_parent, parent = self._get_parent(node)
        if not has_parent:
            self.pos[node][0] = 0
        else:
            self.pos[node][0] = self.pos[parent[0]][0] + self.mod[node]
        has_child, children = self._get_children(node)
        if has_child:
            for child in children:
                self._compute_x(child)

    def _get_children(self, node):
        children = list(self.G.successors(node))
        has_child = len(children) > 0
        return has_child, children

    def _get_parent(self, node):
        parents = list(self.G.predecessors(node))
        has_parent = len(parents) > 0
        return has_parent, parents

# Beispielverwendung
G = nx.DiGraph()
mod = {}

# Add nodes and edges
root = 'Sandwich'
G.add_edge('Sandwich', 'Brooooooooooooooooooooottt')
G.add_edge('Sandwich', 'Käääääääääääääääääääääse')
G.add_edge('Sandwich', 'Salat')
G.add_edge('Sandwich', 'Tomate')
G.add_edge('Sandwich', 'Schinken')
G.add_edge('Brooooooooooooooooooooottt', 'Dinkelbrot')
G.add_edge('Brooooooooooooooooooooottt', 'Vollkornbrot')
G.add_edge('Käääääääääääääääääääääse', 'Emmentaler')
G.add_edge('Käääääääääääääääääääääse', 'Gouda')
G.add_edge('Käääääääääääääääääääääse', 'Bergkäse')
G.add_edge('Salat', 'Eisbergsalat')
G.add_edge('Salat', 'Rucola')
G.add_edge('Salat', 'Greek Salad')


calculator = GraphDistanceCalculator(G, root)
pos = calculator.compute_distances()

# Zeichnen des Graphen
import matplotlib.pyplot as plt
import matplotlib.patches as patches

nx.draw(G, pos, with_labels=True, node_size=3000, node_color='skyblue', font_size=10, arrows=True)
plt.show()
# Draw the graph with rectangles
fig, ax = plt.subplots()
for node, (x, y) in pos.items():
    ax.add_patch(patches.Rectangle((x-0.15, y-0.05), 0.3, 0.1, edgecolor='black', facecolor='skyblue'))
    ax.text(x, y, node, horizontalalignment='center', verticalalignment='center', fontsize=10, fontweight='bold')
# patches.Rectangle((x, y), width, height, edgecolor='black')
# x, y is the lower left corner -> muss width/2 und height/2 sein

# Draw edges
for edge in G.edges():
    start_pos = pos[edge[0]]
    end_pos = pos[edge[1]]
    print(start_pos, end_pos)
    start_pos = (start_pos[0], start_pos[1] - 0.05)
    end_pos = (end_pos[0], end_pos[1] + 0.05)
    ax.annotate("",
                xy=end_pos, xycoords='data',
                xytext=start_pos, textcoords='data',
                arrowprops=dict(arrowstyle="-", color="black", lw=1.5))

ax.set_xlim(-0.1, 1.1)
ax.set_ylim(-1.1, 0.1)
ax.set_aspect('equal')
plt.axis('off')
plt.show()