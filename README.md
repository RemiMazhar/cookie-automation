# Auto Cookie Cookiator
Parce que la taille, ça compte, voici une manière objective de mesurer et compter automatiquement des cookies.  
  
le programme prend en entrée une photo des cookies, une zone de travail, une échelle, et la masse totale, et retourne:
- la même photo avec les cookies entourés et numéroteés
- une feuille excel avec le diamètre et la rotondité de chaque cookie, et quelques données statistiques
- des graphiques représentant la distribution des diamètres et des rotondités
- 2 images intermédiaires pour montrer différentes étapes du processus

Il a déjà été utilisé pour départager un débat sur qui avait fait le plus de cookies (j'en avais fait 317, j'ai gagné, et bim Julie).

## Sommaire
- [Auto Cookie Cookiator](#auto-cookie-cookiator)
  - [Sommaire](#sommaire)
  - [Comment ça marche ?](#comment-ça-marche-)
  - [Détail des données statistiques calculées](#détail-des-données-statistiques-calculées)
  - [Limites](#limites)
  - [Ma recette de cookies (pour ~42 cookies)](#ma-recette-de-cookies-pour-42-cookies)
    - [Ingrédients](#ingrédients)
    - [Recette](#recette)
  - [Installation](#installation)
    - [Installation via pip](#installation-via-pip)
    - [Installation via conda](#installation-via-conda)
    - [Installation de typst](#installation-de-typst)
  - [Erreurs connues](#erreurs-connues)
  - [Train votre propre modèle (optionnel)](#train-votre-propre-modèle-optionnel)


## Comment ça marche ?
C'est tout con: on part du principe que la table est blanche et que les cookies le sont pas, donc il suffit de mesurer et numéroter les composantes connexes de pixels pas blancs.  

En vrai il y a quand même quelques subtilités:
- la table est jamais vraiment blanche, donc en fait on cherche à mesurer si un pixel est "à peu près gris-blanc", pour ça on passe au format HSV et on dit qu'un pixel est "blanc" si sa saturation (S) est assez faible (on pourrait aussi vérifier que sa valeur (V) est assez grande, mais expérimentalement ça marche pas trop parce que ça dépend beaucoup de l'éclairage). Ça se généralise facilement à d'autres couleurs de table que le blanc en mesurant à la fois la différence de H de S et de V, et en calculant une moyenne pondérée des différences pour établir un score qui mesure l'écart à la couleur de la table.
- on applique un flou gaussien avant de chercher les pixels blancs pour avoir des contours un peu plus nets
- souvent il y a d'autres trucs pas blancs sur la photo (ex: tout ce qui est autour de la table), donc l'utilisateur doit définir une "zone de travail" qui inclut les cookies et exclut les autres trucs pas blancs
- pour mesurer le diamètre d'un cookie, le diamètre au sens topologique du terme serait pas très représentatif de la taille du cookie (genre on pourrait faire un cookie très fin et très long pour augmenter artificiellement le diamètre). À la place on mesure l'aire A du cookie, et on appelle "diamètre du cookie" le diamètre du cercle de même aire $\left(d = 2 \times \sqrt\frac{A}{\pi}\right)$.
- On trouve souvent des composantes connexes "parasites" (ex: des miettes, le sol autour de la table...) qu'on ne peut pas facilement exclure de la zone de travail. Pour les ignorer, on considère que seules les composantes connexes qui mesurent entre 3 et 15cm de diamètre sont réllement des cookies
- au niveau de la numérotation, c'est super chiant si les cookies sont numérotés dans un ordre aléatoire. On pourrait les trier par abscisse croissante, mais en supposant que les cookies sont organisés en rectangle ça reste pas super facile à lire, on préférerait que ce soit en sens de lecture, ce qui est non trivial parce que 2 cookies ont jamais des ordonnées parfaitement égales. Donc on numérote les cookies selon une relation d'ordre sur les points du plan définie de la manière suivante: soit $P$ de coordonnées $(x,y)$ et $Q$ de coordonnées $(x',y')$. On dit que $P \leq Q$ ssi $(y + T < y')$ ou $(\mid y-y'\mid \leq T \text{ et } x \leq x')$, avec T une constante de l'ordre de grandeur de la différence d'ordonnée entre 2 cookies de la même ligne.
- On appelle rotondité le rapport entre l'aire d'un cookie et l'aire de son cercle circonscrit. Ça donne un score entre 0 et 1, l'idée est qu'un cookie est considéré comme peu rond s'il prend beaucoup de place comparé à un cookie rond de même aire.
## Détail des données statistiques calculées
- diamètre moyen : la moyenne des diamètres
- écart-type du diamètre : l'écart-type des diamètres
- rotondité moyenne : la moyenne des rotondités
- écart-type de la rotondité : l'écart-type des rotondités
- masse totale : la masse totale des cookies (à mesurer manuellement)
- quantité totale : la quantité de cookies en mol, i.e. le nombre de cookies divisé par le nombre d'Avogadro
- surface totale : la somme des aires des cookies
- masse moyenne d'un cookie : masse totale divisée par le nombre de cookies
- masse molaire : masse d'une mol de cookies (i.e. masse totale divisée par la quantité totale)
- masse surfacique : masse totale divisée par surface totale
- surface molaire : l'aire occupée par 1 mol de cookies, i.e. surface totale divisée par quantité totale
- rayon de schwarschild : il faudrait compresser les cookies dans une sphère de ce rayon pour en faire un trou noir
- rayon de schwarschild molaire : rayon de Schwarschild de 1 mol de cookies. Le rayon de Schwarschild étant proportionnel à la masse, la mesure à vraiment un sens : le rayon de notre trou noir augmente de cette valeur pour chaque mol de cookies supplémentaire

## Limites
- les mesures sont faites en supposant que la photo est une carte à l'échelle de la table, ce qui n'est vrai que dans l'approximation que la photo est prise parfaitement à la verticale et de très loin
- on ne mesure que la surface des cookies, donc si on ne se fie qu'au programme des cookies très fins et très plats paraitront plus gros que des cookies bien épais mais un peu moins étalés. On peut aussi faire semblant que c'est fait exprès pour décourager l'usage excessif de levure pour gonfler les cookies artificiellement
- ça marche pas si les cookies sont trop blancs ou que la table est pas assez blanche => On y travaille dessus avec de l'IA !
- si les cookies sont trop proches les uns des autres le programme arrive pas à les différencier; c'est probablement le plus gros inconvénient, parce que du coup c'est très très chiant de tous les disposer pour la photo => On y travaille dessus avec de l'IA !
- la mesure de rotondité est un peu arbitraire. Perso je l'aime bien, mais ça donne des résultats un peu surprenant, par exemple : un cookie en forme de pacman aura une assez bonne rotondité, alors qu'un cookie en forme de disque avec une excroissance en aura une très mauvaise.
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
- faire ramollir (/!\ pas fondre /!\\) le beurre, $+\infty$ min à température ambiante ou quelques secondes au micro-ondes
- mélanger le beurre, le sucre, le sucre vanillé et la levure jusqu'à avoir un mélange homogène
- rajouter les oeufs et la farine, mélanger (avec les mains c'est souvent plus facile selon à quel point le beurre est mou)
- incorporer le chocolat et mélanger
- sur une plaque recouverte de papier cuisson, faire des boules (taille au choix) bien espacées (ils s'étalent en cuisant)
- mettre au four à 180° pour ~15min jusqu'à ce qu'ils soient un peu dorés (NE PAS SE FIER au temps de cuisson d'une recette, ça dépend beaucoup du four il faut plutôt se fier à l'aspect.)
- en donner à Rémi

## Installation
Ce projet utilise:
- Python 3.12
- typst (pour générer le rapport en PDF)

### Installation via pip
Pour utiliser ce projet via pip, veuillez utiliser la commande suivante:
```bash
pip install -r requirements.txt
```
**Veuillez noter qu'il est recommandé d'installer ce projet avec un environnement conda pour éviter énormément de problème avec les dépendances qui requièrent de la compilation sur votre machine.**
_(Pro tip: Sur linux, vous évitez beaucoup de ces problèmes)_

### Installation via conda
Avec conda:
```bash
conda create -n cookies -c pytorch -c nvidia -c conda-forge python=3.12 pytorch=2.5.1 torchvision pytorch-cuda=11.8 ultralytics typst-py onnx onnxruntime && conda activate cookies
```
_NB: Adaptez cette commande notamment si vous n'avez pas besoin de la dépendance pytorch-cuda si vous n'avez pas de GPU Nvidia_

Pour installer conda, veuillez vous référer au site officiel: https://conda-forge.org/download/ & https://github.com/conda-forge/miniforge/blob/main/README.md#requirements-and-installers

### Installation de typst
Typst est un langage de mise en page similaire à LaTeX, mais plus moderne et plus simple d'utilisation. Pour l'installer, veuillez suivre les instructions sur le repo officiel: https://github.com/typst/typst/blob/main/README.md#installation 
Tout ce qui importe est d'avoir la commande `typst` disponible dans votre PATH.

## Erreurs connues
- Sous linux et avec Wayland, vous pourriez avoir un warning voire une erreur du style:
```
qt.qpa.plugin: Could not find the Qt platform plugin "wayland" in ""
```
Cela est peut-être dû au fait que certaines librairies Qt ne sont pas installées par défaut comme `qtwayland5` ou `qtwayland6` (à adapter selon votre distro).

Si cela ne suffit pas, vous pouvez toujours forcer l'utilisation de XWayland en lançant votre script avec la variable d'environnement `QT_QPA_PLATFORM`:
```bash
QT_QPA_PLATFORM=xcb python ...
```

## Train votre propre modèle (optionnel)
Explication soon...
