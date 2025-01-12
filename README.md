# Auto Cookie Cookiator
Parce que la taille, ça compte, voici une manière objective de mesurer et compter automatiquement des cookies.  
  
le programme prend en entrée une photo des cookies, une zone de travail, et une échelle, et retourne:
- la même photo avec les cookies entourés et numéroteés
- une feuille excel avec le diamètre de chaque cookie, le diamètre moyen et l'écart-type
- un histogramme représentant la distribution des diamètres
- 2 images intermédiaires pour montrer différentes étapes du processus

Il a déjà été utilisé pour départager un débat sur qui avait fait le plus de cookies (j'en avais fait 317, j'ai gagné, et bim Julie).

## Comment ça marche ?
C'est tout con: on part du principe que la table est blanche et que les cookies le sont pas, donc il suffit de mesurer et numéroter les composantes connexes de pixels pas blancs.  

En vrai il y a quand même quelques subtilités:
- la table est jamais vraiment blanche, donc en fait on cherche à mesurer si un pixel est "à peu près gris-blanc", pour ça on passe au format HSV et on dit qu'un pixel est "blanc" si sa saturation (S) est assez faible (on pourrait aussi vérifier que sa valeur (V) est assez grande, mais expérimentalement ça marche pas trop parce que ça dépend beaucoup de l'éclairage). Ça se généralise facilement à d'autres couleurs de table que le blanc en mesurant à la fois la différence de H de S et de V, et en calculant une moyenne pondérée des différences pour établir un score qui mesure l'écart à la couleur de la table.
- on applique un flou gaussien avant de chercher les pixels blancs pour avoir des contours un peu plus nets
- souvent il y a d'autres trucs pas blancs sur la photo (ex: tout ce qui est autour de la table), donc l'utilisateur doit définir une "zone de travail" qui inclut les cookies et exclut les autres trucs pas blancs
- pour mesurer le diamètre d'un cookie, le diamètre au sens topologique du terme serait pas très représentatif de la taille du cookie (genre on pourrait faire un cookie très fin et très long pour augmenter artificiellement le diamètre). À la place on mesure l'aire A du cookie, et on appelle "diamètre du cookie" le diamètre du cercle de même aire (d = 2 * sqrt(A / pi)).
- au niveau de la numérotation, c'est super chiant si les cookies sont numérotés dans un ordre aléatoire. On pourrait les trier par abscisse croissante, mais en supposant que les cookies sont organisés en rectangle ça reste pas super facile à lire, on préférerait que ce soit en sens de lecture, ce qui est non trivial parce que 2 cookies ont jamais des ordonnées parfaitement égales. Donc on numérote les cookies selon une relation d'ordre sur les points du plan définie de la manière suivante: soit P de coordonnées (x,y) et Q de coordonnées (x',y'). On dit que P ≤ Q ssi (y + T < y') ou (|y-y'| ≤ T et x ≤ x'), avec T une constante de l'ordre de grandeur de la différence d'ordonnée entre 2 cookies de la même ligne.

## Limites
- les mesures sont faites en supposant que la photo est une carte à l'échelle de la table, ce qui n'est vrai que dans l'approximation que la photo est prise parfaitement à la verticale et de très loin
- on ne mesure que la surface des cookies, donc si on ne se fie qu'au programme des cookies très fins et très plats paraitront plus gros que des cookies bien épais mais un peu moins étalés. On peut aussi faire semblant que c'est fait exprès pour décourager l'usage excessif de levure pour gonfler les cookies artificiellement
- ça marche pas si les cookies sont trop blancs ou que la table est pas assez blanche
- si les cookies sont trop proches les uns des autres le programme arrive pas à les différencier; c'est probablement le plus gros inconvénient, parce que du coup c'est très très chiant de tous les disposer pour la photo
- le programme a tendance à trouver les cookies de Julie plus gros que les miens, il faut absolument changer ça

## Ma recette de cookies (pour ~42 cookies)
### Ingrédients
- 200g de sucre
- 225g de sucre roux (oui c'est beaucoup de sucre, c'est pour ça que c'est bon)
- 250g de beurre (oui c'est beaucoup de beurre, c'est pour ça que c'est bon)
- 400g de chocolat coupé en morceaux (oui c'est beaucoup de chocolat, c'est pour ça que c'est bon)
- 450g de farine
- 2 oeufs
- 2 sachets de sucre vanillé (ou de l'extrait de vanille si t'es riche)
- 1 demi sachet de levure
- papier cuisson (c'est pas un ingrédient mais je le mets parce que j'oublie toujours d'en acheter quand je fais les courses pour des cookies)
### Recette
- faire ramollir (/!\ pas fondre /!\) le beurre, +∞ min à température ambiante ou quelques secondes au micro-ondes
- mélanger le beurre, le sucre, le sucre vanillé et la levure jusqu'à avoir un mélange homogène
- rajouter les oeufs et la farine, mélanger (avec les mains c'est souvent plus facile selon à quel point le beurre est mou)
- incorporer le chocolat et mélanger
- sur une plaque recouverte de papier cuisson, faire des boules (taille au choix) bien espacées (ils s'étalent en cuisant)
- mettre au four à 180° pour ~15min jusqu'à ce qu'ils soient un peu dorés (NE PAS SE FIER au temps de cuisson d'une recette, ça dépend beaucoup du four il faut plutôt se fier à l'aspect.)
- en donner à Rémi
