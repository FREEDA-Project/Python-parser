from pydantic import BaseModel

# Budget definition - Budget is a pair b = <cost,gCO2-eq/KWh> which expresses
# how much the application administrator is willing to pay for the deployment

class Budget(BaseModel):
    cost: float
    carbon: float
