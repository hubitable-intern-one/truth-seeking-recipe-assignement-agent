from models.recipe_context import UserDetails, Lifestyle

TEST_PROFILES = [
    # 1. Diabetes Type 1
    # Context: Insulin dependent, needs precise carb counting.
    UserDetails(
        label="The Type 1 Diabetic",
        height=170.0, weight=68.0, age=30,
        lifestyle=Lifestyle.ACTIVE,
        conditions=["Diabetes Type 1", "Insulin Dependent"]
    ),

    # 2. Diabetes Type 2
    # Context: Insulin resistance, focus on weight management and low GI.
    UserDetails(
        label="The Type 2 Diabetic",
        height=175.0, weight=105.0, age=50,
        lifestyle=Lifestyle.SEDENTARY,
        conditions=["Diabetes Type 2", "Obesity"]
    ),

    # 3. Weight Loss Program
    # Context: Caloric deficit goal, high satiety needed.
    UserDetails(
        label="Weight Loss Goal",
        height=168.0, weight=90.0, age=35,
        lifestyle=Lifestyle.SEDENTARY,
        conditions=["Obesity", "Caloric Deficit Goal"]
    ),

    # 4. Weight Gain Program
    # Context: Caloric surplus goal, high protein/carb needs.
    UserDetails(
        label="Weight Gain / Muscle Build",
        height=182.0, weight=70.0, age=24,
        lifestyle=Lifestyle.VERY_ACTIVE,
        conditions=["Underweight", "High Calorie Goal"]
    ),

    # 5. Dialysis Patient
    # Context: Needs HIGH protein but strict fluid/potassium/sodium limits.
    UserDetails(
        label="The Dialysis Patient",
        height=175.0, weight=75.0, age=60,
        lifestyle=Lifestyle.SEDENTARY,
        conditions=["End Stage Renal Disease", "Hemodialysis"]
    ),

    # 6. Hypertension (High BP)
    # Context: Sodium restriction (DASH diet) is the priority.
    UserDetails(
        label="The Hypertensive Patient",
        height=178.0, weight=85.0, age=55,
        lifestyle=Lifestyle.SEDENTARY,
        conditions=["Hypertension", "High Cholesterol"]
    )
]