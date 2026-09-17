from engine.oracle_engine import OracleEngine


oracle = OracleEngine()

result = oracle.evaluate()

print()
print("======================================")
print("       RAINGUARD ORACLE ENGINE")
print("======================================")

print(
    "Decision:",
    result["decision"]
)

print(
    "Trusted Rainfall:",
    result["trusted_rainfall_mm"]
)

print(
    "Valid Sources:",
    result["valid_source_count"]
)

print(
    "Required Sources:",
    result["required_source_count"]
)

print(
    "Reason:",
    result["reason"]
)

print()
print("Sources:")

for source in result["all_sources"]:

    print(
        source["source_name"],
        "->",
        source["rainfall_mm"],
        "mm"
    )

print()