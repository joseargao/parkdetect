

class Vehicle:

    def __init__(self, vehicle_id, zone_id) -> None:
        self.id = vehicle_id
        self.zone_ids = [] if zone_id is None else [zone_id]

    def add_zone(self, zone_id):
        ''' Add a zone id to the list of zones where a vehicle parked,
        unless it was already listed

        @param  zone_id    zone id where a vehicle had parked

        @return None '''
        if zone_id and zone_id not in self.zone_ids:
            self.zone_ids.append(zone_id)
            # print(f"Added {zone_id} to vehicle[{self.id}].zone_ids: {self.zone_ids}")


class ParkCounter:

    def __init__(self) -> None:
        self.vehicles = []

    def add_vehicle(self, vehicle_id, zone_id=None):
        ''' Add a vehicle id to the list of vehicles detected, unless it had already
        been found

        @param  vehicle_id       id associated with a detected vehicle
        @param  zone_id          zone id where the detected vehicle had parked

        @return None '''

        found = next((v for v in self.vehicles if v.id == vehicle_id), None)
        if found:
            found.add_zone(zone_id)
        else:
            self.vehicles.append(Vehicle(vehicle_id, zone_id))
            # print(f"Added {vehicle_id} to self.vehicles: {[v.id for v in self.vehicles]}")

    def get_count(self, zone_id=None):
        ''' Get the count of all vehicles detected, or all vehicles that had occupied a zone

        @param  zone_id          zone id where detected vehicles had parked

        @return Total number of vehicles detected, or number of vehicles that parked in a zone '''

        return len([v for v in self.vehicles if zone_id in v.zone_ids]) if zone_id else len(self.vehicles)

    def reset_count(self):
        ''' Reset the count of all vehicles detected as well as all vehicles that had occupied a zone

        @param  None

        @return None '''

        self.vehicles.clear()
