from models.schemas import Car, Part, CarPart

FAKE_CARS = [
    Car(id=1, make="יונדאי", model="i30", year=2016, engine_size="1.6L", fuel_type="בנזין"),
    Car(id=2, make="טויוטה", model="קורולה", year=2018, engine_size="1.8L", fuel_type="היברידי"),
]

FAKE_PARTS = [
    Part(id=1, name="פילטר אוויר", part_number="28113-2P100", category="פילטרים"),
    Part(id=2, name="פילטר שמן", part_number="26300-35504", category="פילטרים"),
]

CAR_PARTS_MAPPING = {
    1: [
        CarPart(car_id=1, part=FAKE_PARTS[0], maintenance_interval_km=15000, is_required_for_test=True),
        CarPart(car_id=1, part=FAKE_PARTS[1], maintenance_interval_km=10000, is_required_for_test=False),
    ]
}