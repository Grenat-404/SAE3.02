class IntersectionOSM:
    """Représente un carrefour détecté pendant la lecture OSM."""

    def __init__(
        self,
        node_id,
        latitude,
        longitude,
        noms_routes,
        ways,
        nombre_branches
    ):
        self.__node_id = node_id
        self.__latitude = latitude
        self.__longitude = longitude
        self.__noms_routes = noms_routes
        self.__ways = ways
        self.__nombre_branches = nombre_branches

    def get_node_id(self):
        return self.__node_id

    def get_latitude(self):
        return self.__latitude

    def get_longitude(self):
        return self.__longitude

    def get_noms_routes(self):
        return self.__noms_routes

    def get_ways(self):
        return self.__ways

    def get_nombre_branches(self):
        return self.__nombre_branches

    def get_nom_affichage(self):
        noms = []

        for nom in self.__noms_routes:
            if nom not in noms:
                noms.append(nom)

        noms_valides = [
            nom
            for nom in noms
            if nom != "Route sans nom"
        ]

        if len(noms_valides) == 0:
            return f"Carrefour #{self.__node_id}"

        if (
            len(noms_valides) == 1
            and "Route sans nom" in noms
        ):
            return (
                noms_valides[0]
                + " × Route sans nom"
            )

        return " × ".join(noms)