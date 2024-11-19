class FeatureModel:
    def __init__(self):
        self.features = {}
        self.relations = []

    def add_feature(self, feature_name, cardinality=(1, 1)):
        self.features[feature_name] = cardinality

    def remove_feature(self, feature_name):
        if feature_name in self.features:
            del self.features[feature_name]
            self.relations = [(p, c) for p, c in self.relations if p != feature_name and c != feature_name]

    def add_relation(self, parent, child):
        self.relations.append((parent, child))

    def remove_relation(self, parent, child):
        self.relations = [(p, c) for p, c in self.relations if not (p == parent and c == child)]

    def save_to_uvl(self, file_path):
        with open(file_path, 'w') as file:
            file.write(self.to_uvl())

    def load_from_uvl(self, file_path):
        with open(file_path, 'r') as file:
            content = file.read()
            self.from_uvl(content)

    def to_uvl(self):
        uvl_content = "features:\n"
        for feature, cardinality in self.features.items():
            uvl_content += f"  {feature}: [{cardinality[0]}, {cardinality[1]}]\n"
        uvl_content += "relations:\n"
        for parent, child in self.relations:
            uvl_content += f"  {parent} -> {child}\n"
        return uvl_content

    def from_uvl(self, content):
        self.features.clear()
        self.relations.clear()
        lines = content.splitlines()
        section = None
        for line in lines:
            if line.startswith("features:"):
                section = "features"
            elif line.startswith("relations:"):
                section = "relations"
            elif section == "features":
                feature, cardinality = line.strip().split(": ")
                cardinality = tuple(map(int, cardinality.strip("[]").split(", ")))
                self.features[feature] = cardinality
            elif section == "relations":
                parent, child = line.strip().split(" -> ")
                self.relations.append((parent, child))