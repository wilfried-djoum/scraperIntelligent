from pydantic import BaseModel

class BaseProfile(BaseModel):
    first_name: str
    last_name: str
    enterprise: str

    def getFullName(self):
        return f"{self.first_name} {self.last_name}"
