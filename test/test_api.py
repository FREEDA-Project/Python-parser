import requests
import pprint
import sys

recipe = """Per realizzare la pasta alla gricia per prima cosa preparate il guanciale: tagliatelo a fette dello spessore di mezzo cm 1, poi rimuovete la cotenna 2 e ricavate delle listarelle 3. Mettete sul fuoco una pentola di acqua da salare a bollore.
Versate il guanciale in una padella ben calda 4 e rosolate a fiamma medio-alta per circa 10 minuti, mescolando spesso per non farlo bruciare 5. Quando sarà appena dorato rimuovete il guanciale e mettetelo da parte, lasciando il fondo di cottura nella padella 6.
Nel frattempo l’acqua per la pasta sarà arrivata a bollore, quindi cuocete i rigatoni per 2-3 minuti in meno rispetto al tempo indicato sulla confezione 7. Grattugiate il Pecorino con una grattugia a maglie strette 8 e tenete da parte. Versate un mestolo dell’acqua di cottura della pasta nella padella col fondo ancora caldo del guanciale 9 e ruotatela per creare un’emulsione.
Scolate i rigatoni nella padella 10 e ultimate la cottura saltando e mescolando spesso, in modo che l’amido rilasciato dalla pasta si amalgami al grasso del condimento creando una cremina 11. Quando la pasta sarà al dente, togliete la padella dal fuoco e aggiungete a pioggia il Pecorino grattugiato 12.
Quindi diluite subito con poca acqua di cottura della pasta calda 13, mescolate rapidamente così da ad ottenere un condimento fluido e cremoso. In ultimo unite il guanciale rosolato 14 e date un’ultima mescolata 15.
Impiattate subito 16 e completate a piacere con pepe macinato 17. La vostra pasta alla gricia è pronta per essere gustata 18!"""

if len(sys.argv) > 1:
    # read recepie from input
    # multiline recepie that ends with  END!
    print("Enter the recipe (END! to finish):")
    recipe = ""
    while True:
        line = input()
        if line == "END!":
            break
        recipe += line + "\n"


response = requests.post("http://localhost:8000/recipe", json={"recipe": recipe})
breakpoint()
pprint(response.json())