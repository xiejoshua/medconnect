from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()


class Doctor(BaseModel):
    id: int
    name: str
    specialty: str
    hospital: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    conditions: Optional[List[str]] = []


DOCTORS = [
    Doctor(id=1, name='Dr. Alice Nguyen', specialty='Genetics', hospital='Central University Hospital', email='alice.nguyen@example.org', phone='555-0101', conditions=['Fabry disease', 'Gaucher disease']),
    Doctor(id=2, name='Dr. Ben Carter', specialty='Neurology', hospital='Westside Medical', email='ben.carter@example.org', phone='555-0102', conditions=['Wilson disease', 'Huntington disease']),
    Doctor(id=3, name='Dr. Chen Li', specialty='Metabolic Disorders', hospital="Children's Research Clinic", email='chen.li@example.org', phone='555-0103', conditions=['Phenylketonuria', 'Maple syrup urine disease']),
    Doctor(id=4, name='Dr. Dana Smith', specialty='Rheumatology', hospital='North Medical Center', email='dana.smith@example.org', phone='555-0104', conditions=['Ehlers-Danlos syndrome', 'Marfan syndrome']),
]


@app.get('/api/search', response_model=List[Doctor])
def search(q: str = Query(..., min_length=1)):
    qlow = q.lower()
    results = []
    for d in DOCTORS:
        if qlow in d.specialty.lower():
            results.append(d)
            continue
        for cond in d.conditions or []:
            if qlow in cond.lower():
                results.append(d)
                break
    return results
