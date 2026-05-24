from vector_store import add_documents

docs = [
    {"id": "1", "text": "Erling Haaland joined Manchester City in 2022 and scored 36 Premier League goals in his debut season, breaking the all-time record."},
    {"id": "2", "text": "Arsenal's high press under Mikel Arteta relies on quick transitions and pressing triggers, particularly after losing the ball in the final third."},
    {"id": "3", "text": "The 4-3-3 formation is widely used in modern football. It provides width through wingers and allows fullbacks to overlap."},
    {"id": "4", "text": "Mohamed Salah has been Liverpool's top scorer for six consecutive seasons. He is known for his pace, inside left movement and clinical finishing."},
    {"id": "5", "text": "Manchester City's inverted wingers tactic under Pep Guardiola involves wide players cutting inside onto their stronger foot to shoot or combine centrally."},
    {"id": "6", "text": "The Premier League was founded in 1992. Manchester United have won it the most times with 13 titles since its formation."},
    {"id": "7", "text": "Tiki-taka is a style of play pioneered by Barcelona and Spain, based on short passing, movement, and maintaining possession to create space."},
    {"id": "8", "text": "A false nine is a centre-forward who drops deep to receive the ball, dragging defenders out of position and creating space for midfielders to run into."}
]

add_documents(docs)
print("Vector store seeded.")