NO_CREDS = (
    "Error: No CloudRadial credentials. Send the X-CloudRadial-Public-Key and "
    "X-CloudRadial-Private-Key headers."
)


def paging_params(
    skip: int | None = None,
    take: int | None = None,
    order: str | None = None,
    direction: str | None = None,
    filter_field: str | None = None,
    condition: str | None = None,
    value: str | None = None,
) -> dict:
    """Build the common Skip/Take/Order/Direction/Filter/Condition/Value query params.

    These are documented as common list-endpoint parameters across the
    CloudRadial API (see developers.cloudradial.com/docs/getting-started).
    """
    return {
        "Skip": skip,
        "Take": take,
        "Order": order,
        "Direction": direction,
        "Filter": filter_field,
        "Condition": condition,
        "Value": value,
    }
