from tau2.environment.toolkit import ToolKitBase

class DivemotorTools(ToolKitBase):

    def get_user_info(self, user_id: str):
        return self.db.users.get(user_id)

    def search_vehicles(self, brand: str, max_price: float):
        return [
            v for v in self.db.vehicles.values()
            if v.brand.lower() == brand.lower() and v.price <= max_price
        ]

    def get_vehicle_details(self, vehicle_id: str):
        return self.db.vehicles.get(vehicle_id)

    def create_lead(self, user_id: str, interest: str):
        new_id = str(len(self.db.leads) + 1)
        self.db.leads[new_id] = {
            "lead_id": new_id,
            "user_id": user_id,
            "interest": interest
        }
        return self.db.leads[new_id]

    def book_test_drive(self, user_id: str, vehicle_id: str, date: str):
        if user_id not in self.db.users or vehicle_id not in self.db.vehicles:
            return None

        new_id = str(len(self.db.test_drives) + 1)
        self.db.test_drives[new_id] = {
            "test_id": new_id,
            "user_id": user_id,
            "vehicle_id": vehicle_id,
            "date": date
        }
        return self.db.test_drives[new_id]

    def request_financing(self, user_id: str, vehicle_id: str, income: float):
        if income < 1500:
            return {"status": "rejected"}

        return {"status": "approved"}