Kurze Zusammenfassung:
in problems/pressure_pipe_03.py kannst du deine Probleml�sung implementieren: 
	compute_solution(): L�st das Problem und gibt die L�sung in einem dictonary zur�ck
	index(): dort werden mit Parameter() die Parameter f�r die Slider definiert
	plot(): plot Funktion f�r die Ausgabe von compute_solution() 

in templates/problems/pressure_pipe_03.html werden die Texte auf der Website angepasst
Latex code ist dort mit \( my latex code \)

in templates/problems/pressure_pipe_03_solution.html wird der sich aktualierende L�sungsblock angepasst
Hier kann in Latex auf python Variablen von solution zugegriffen und formatiert werden: $$ my latex code {{my python code}} my latex code $$

in hydraulics.py bzw. geometry.py findest du bereits definierte funktion wie zB Strickler, Berechnung von Lamnda etc.

in dict.py gibt es ein englisches bzw. deutsches dictionary mit identischen Keys, hier werden f�r die Plots s�mtliche Bezeichnungen hinterlegt um sie f�r beide Sprachen verf�gbar zu machen

in unity.py sind Einheiten mit Umrechnungen bzw auch Konstanten definiert