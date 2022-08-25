Kurze Zusammenfassung:
in problems/pressure_pipe_03.py kannst du deine Problemlösung implementieren: 
	compute_solution(): Löst das Problem und gibt die Lösung in einem dictonary zurück
	index(): dort werden mit Parameter() die Parameter für die Slider definiert
	plot(): plot Funktion für die Ausgabe von compute_solution() 

in templates/problems/pressure_pipe_03.html werden die Texte auf der Website angepasst
Latex code ist dort mit \( my latex code \)

in templates/problems/pressure_pipe_03_solution.html wird der sich aktualierende Lösungsblock angepasst
Hier kann in Latex auf python Variablen von solution zugegriffen und formatiert werden: $$ my latex code {{my python code}} my latex code $$

in hydraulics.py bzw. geometry.py findest du bereits definierte funktion wie zB Strickler, Berechnung von Lamnda etc.

in dict.py gibt es ein englisches bzw. deutsches dictionary mit identischen Keys, hier werden für die Plots sämtliche Bezeichnungen hinterlegt um sie für beide Sprachen verfügbar zu machen

in unity.py sind Einheiten mit Umrechnungen bzw auch Konstanten definiert