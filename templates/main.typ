#set page(header: context { if(counter(page).get().at(0)==1) [
  #text(size: 14pt)[23/10/2025]
]})
#set par(justify: true)
#set text(font: "Arial", size: 11pt)
#set page(numbering: "1", number-align: right, paper: "a4")
#set document(title: [Cookies])
#let infos = json(bytes(sys.inputs.infos))


#align(center)[#image("assets/École_polytechnique_signature.svg.png", alt: "Logo X", height: 60%)]

#align(center)[
  #text(size: 48pt)[
    Cookies pour 
    #linebreak()
    CookieS !!!!
  ]
  #v(0.5em)
  #text(size: 24pt)[
    Fish Teknik

  ]
  #text(size: 10pt)[
    Vive la S.E.C.T.E.S
  ]
]


#pagebreak()


#outline(title: "Table des matières")


#pagebreak()
= Introduction
Le présent document décrit les détails techniques relatifs aux *#infos.nb_cookies cookies* faits par *#infos.author* le #infos.date à destination de *#infos.dest*. Il vise à fournir une caractérisation précise de ces produits comestibles, en s’appuyant sur un ensemble de mesures physiques telles que leur diamètre, leur taille, ou encore leur rayon.

Dans une démarche mêlant rigueur scientifique et plaisir gustatif, cette fiche
technique a pour ambition de documenter de manière structurée un échantillon de
cookies réalisés artisanalement. L’objectif est double : d’une part, proposer un retour sur les caractéristiques objectives de la production (afin d’envisager, le cas échéant, une amélioration ou une reproduction des résultats), et d’autre part, offrir aux membres de la section une lecture ludique et informée de ce qui leur a été servi.

Les données ont été obtenues grâce à un programme développé spécifiquement
pour analyser des photographies des cookies. Ce programme détecte les contours
de chaque pièce sur une image de référence calibrée, permettant de les numéroter
et d’en extraire automatiquement le diamètre. Ces données ont ensuite été intégrées dans des fichiers Excel dédiés, qui calcule des statistiques descriptives telles que les moyennes, écarts-types et éventuelles valeurs aberrantes. Ce protocole semi-automatisé permet une analyse rapide, reproductible et relativement fiable, tout en limitant les biais liés à des mesures manuelles.

Ce document s’adresse donc à toute personne curieuse d’en savoir plus sur la nature physique des cookies dégustés le #infos.date, qu’il s’agisse de fins gourmets, de futurs pâtissiers scientifiques ou simplement de membres de la section en quête d’une lecture originale.


#pagebreak()
= Méthodologie
Détails disponibles ici : #link("https://github.com/RemiMazhar/cookie-automation")
== Fonctionnement du programme
C'est tout con: on part du principe que la table est blanche et que les cookies le sont pas,
donc il suffit de mesurer et numéroter les composantes connexes de pixels pas blancs.

En vrai il y a quand même quelques subtilités:

- la table est jamais vraiment blanche, donc en fait on cherche à   mesurer si un pixel est "à peu près gris-blanc", pour ça on passe au format HSV et on dit qu'un pixel est "blanc" si sa saturation (S) est assez faible (on pourrait aussi vérifier que sa valeur (V) est assez grande, mais expérimentalement ça marche pas trop parce que ça dépend beaucoup de l'éclairage).
  
  Ça se généralise facilement à d'autres couleurs de table que le blanc en mesurant à la fois la différence de H de S et de V, et en calculant une moyenne pondérée des différences pour établir un score qui mesure l'écart à la couleur de la table.

- on applique un flou gaussien avant de chercher les pixels blancs pour avoir des contours un peu plus nets
- souvent il y a d'autres trucs pas blancs sur la photo (ex: tout ce qui est autour de la table), donc l'utilisateur doit définir une "zone de travail" qui inclut les cookies et exclut les autres trucs pas blancs
- pour mesurer le diamètre d'un cookie, le diamètre au sens topologique du terme serait pas très représentatif de la taille du cookie (genre on pourrait faire un cookie très fin et très long pour augmenter artificiellement le diamètre). À la place on mesure l'aire A du cookie, et on appelle "diamètre du cookie" le diamètre du cercle de même aire $(d = 2 times sqrt(A / pi))$.
- On trouve souvent des composantes connexes "parasites" (ex: des miettes, le sol autour de la table...) qu'on ne peut pas facilement exclure de la zone de travail. Pour les ignorer, on considère que seules les composantes connexes qui mesurent entre 3 et 15cm de diamètre sont réllement des cookies
- au niveau de la numérotation, c'est super chiant si les cookies sont numérotés dans un ordre aléatoire. On pourrait les trier par abscisse croissante, mais en supposant que les cookies sont organisés en rectangle ça reste pas super facile à lire, on préférerait que ce soit en sens de lecture, ce qui est non trivial parce que 2 cookies ont jamais des ordonnées parfaitement égales. Donc on numérote les cookies selon une relation d'ordre sur les points du plan définie de la manière suivante: soit $P$ de coordonnées $(x,y)$ et $Q$ de coordonnées $(x',y')$. On dit que $P <= Q$ ssi $(y + T < y')$ ou $(|y-y'| <= T " et " x <= x')$, avec T une constante de l'ordre de grandeur de la différence d'ordonnée entre 2 cookies de la même ligne.
- On appelle rotondité le rapport entre l'aire d'un cookie et l'aire de son cercle circonscrit. Ça donne un score entre 0 et 1, l'idée est qu'un cookie est considéré comme peu rond s'il prend beaucoup de place comparé à un cookie rond de même aire.

#pagebreak()
== Détail des données statistiques calculées
*diamètre moyen* : la moyenne des diamètres

*écart-type du diamètre* : l'écart-type des diamètres

*rotondité moyenne* : la moyenne des rotondités

*écart-type de la rotondité* : l'écart-type des rotondités

*masse totale* : la masse totale des cookies (à mesurer manuellement)

*quantité totale* : la quantité de cookie en mol, i.e. le nombre de cookies divisé par le nombre d'Avogadro

*surface totale* : la somme des aires des cookies

*masse moyenne d'un cookie* : masse totale divisée par le nombre de cookies

*masse molaire* : masse d'une mol de cookies (i.e. masse totale divisée par la quantité totale)

*masse surfacique* : masse totale divisée par surface totale

*surface molaire* : l'aire occupée par 1 mol de cookies, i.e. surface totale divisée par quantité totale

*rayon de schwarschild* : il faudrait compresser les cookies dans une sphère de ce rayon pour en faire un trou noir

*rayon de schwarschild molaire* : rayon de Schwarschild de 1 mol de cookies. Le rayon de Schwarschild étant proportionnel à la masse, la mesure à vraiment un sens : le rayon de notre trou noir augmente de cette valeur pour chaque mol de cookies supplémentaire

#pagebreak()
= Données brutes
== Numérotation
#image("../src/out/res.png", alt: "Image numérotée des cookies")

#pagebreak()
== Tableau des diamètres et des rotondités
#let diams = csv("../src/out/diameters.csv")

#table(columns: 3, ..diams.flatten())

#pagebreak()
= Résultats statistiques
== Distribution des diamètres et des rotondités
#image("../src/out/diam_histogram.png", alt: "Histogramme des diamètres", height: 40%)
#image("../src/out/roundness_histogram.png", alt: "Histogramme des rotondités", height: 40%)
#image("../src/out/roundness_diam_scatter.png", alt: "Dispersion rotondité/diamètre")
== Données globales
#let stats = csv("../src/out/stats.csv")
#table(columns: 2, ..stats.flatten())