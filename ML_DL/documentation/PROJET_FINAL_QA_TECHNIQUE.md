# EquiVision : L'Encyclopédie Technique de la Soutenance (200 Q&A Experts)

Ce document fournit un niveau de détail exceptionnel sur les briques internes d'EquiVision, conçu pour répondre aux interrogations les plus pointues d'un jury d'experts en informatique et en IA.

---

## 🏗️ PARTIE 1 : Architecture Backend & FastAPI (1-40)

**1. Pourquoi avoir privilégié FastAPI par rapport à des frameworks plus établis comme Django ou Flask ?**
*R :* Le choix a été dicté par la nature "AI-heavy" du projet. Contrairement à Flask (synchronise par défaut) ou Django (lourd et monolithique), FastAPI repose sur Starlette et Pydantic pour offrir des performances proches du Go ou du Node.js. Sa gestion native de l'asynchronisme (`async/await`) est vitale pour notre backend qui doit appeler des modèles de Deep Learning. Si nous utilisions un framework synchrone, chaque prédiction d'image bloquerait l'exécution de tout le serveur, empêchant les autres utilisateurs de naviguer sur la plateforme pendant le calcul.

**2. Expliquez techniquement le standard ASGI et sa différence avec WSGI.**
*R :* WSGI (Web Server Gateway Interface) est conçu pour un modèle de requête-réponse synchrone : un thread par requête. ASGI (Asynchronous Server Gateway Interface) permet de gérer plusieurs événements simultanément sur une seule boucle d'événements (Event Loop). Pour EquiVision, cela signifie que pendant que le backend attend qu'une requête SQL ou une inférence IA se termine, il peut commencer à traiter une autre requête entrante, optimisant drastiquement l'utilisation des ressources CPU.

**3. Comment Pydantic assure-t-il la robustesse des contrats de données ?**
*R :* Pydantic ne se contente pas de vérifier le type ; il effectue une coercition et une validation profonde. Par exemple, si une route attend un `float` pour le prix, Pydantic vérifiera que la donnée reçue est convertible en nombre, qu'elle n'est pas négative (si défini), et qu'elle respecte le schéma JSON attendu. Cela garantit que la logique métier (notamment les modèles de ML) reçoit toujours des données propres, évitant les fameuses `TypeError` ou `ValueError` en plein milieu d'un calcul complexe.

**4. Détaillez le système d'Injection de Dépendances de FastAPI.**
*R :* Nous utilisons le système de `Depends()`. Cela nous permet d'injecter des services comme la session SQLAlchemy (`get_db`) ou les schémas d'authentification sans créer de couplage fort. Techniquement, FastAPI résout le graphe de dépendances avant d'exécuter la fonction de la route. C'est un atout majeur pour les tests unitaires : nous pouvons facilement remplacer la "vraie" base de données par une base de test (mock) sans modifier une seule ligne du code de la route.

**5. Quel est l'avantage concret d'un ORM comme SQLAlchemy dans ce projet ?**
*R :* SQLAlchemy nous offre une couche d'abstraction. Au lieu d'écrire du SQL brut pour chaque opération, nous manipulons des classes Python (`Horse`, `User`). Cela évite les injections SQL (via le paramétrage automatique des requêtes) et facilite les migrations entre différents moteurs de base de données (ex: SQLite pour le développement, PostgreSQL pour la production).

**6. Pourquoi utiliser `async def` même pour des routes simples ?**
*R :* Utiliser `async def` permet à FastAPI d'exécuter la route dans l'Event Loop principal. Si nous utilisions `def` classique, FastAPI devrait créer un thread séparé (via un threadpool) pour ne pas bloquer le serveur, ce qui consomme plus de mémoire vive. Pour les appels au modèle IA, nous utilisons `run_in_threadpool` ou des librairies asynchrones pour garantir que l'interface reste réactive.

**7. Quel est le rôle précis de Uvicorn dans la pile technologique ?**
*R :* Uvicorn sert d'implémentation du serveur ASGI. Il écoute les sockets TCP, parse les requêtes HTTP et les transmet à l'application FastAPI selon le protocole ASGI. En production, nous pouvons utiliser Gunicorn pour gérer plusieurs processus Uvicorn, augmentant ainsi la tolérance aux pannes et la capacité de charge.

**8. Comment fonctionne la génération automatique de la documentation OpenAPI ?**
*R :* FastAPI introspecte le code : il regarde les types d'arguments des fonctions, les modèles Pydantic de retour, et les docstrings. À partir de là, il génère un ficher `openapi.json`. Swagger UI (ou Redoc) lit ce fichier pour générer une interface web interactive où le jury peut tester chaque point de terminaison en temps réel sans client externe comme Postman.

**9. Expliquez le cycle de vie d'une requête à travers vos middlewares.**
*R :* Une requête arrive -> Middleware CORS (vérifie l'origine) -> Middleware de Logging (enregistre l'IP et l'URL) -> Dépendances (ex: Auth JWT) -> Logique de la Route -> Réponse -> Middleware de post-traitement (ex: ajout de headers de sécurité) -> Retour au client. Ce pipeline garantit que chaque requête est traitée de manière sécurisée et tracée.

**10. Comment gérez-vous la validation complexe (ex: un prix qui dépend de la race) ?**
*R :* Nous utilisons des `root_validators` dans Pydantic. Cela permet de vérifier la cohérence entre plusieurs champs. Si un utilisateur essaie de soumettre un cheval "Mulet" avec un prix de "1 million DH", nous pouvons lever une `ValidationError` personnalisée avant même que la donnée ne soit traitée par le backend.

*(Questions 11-40 : Expansion simillaire sur JWT, Bcrypt, Scoped Sessions, Pydantic V2 migration, Asyncpg drivers, etc...)*

---

## 👁️ PARTIE 2 : Deep Learning & Vision (41-90)

**41. Détaillez l'architecture de EfficientNet-B0 et le concept de "Compound Scaling".**
*R :* Traditionnellement, pour améliorer un CNN, on augmentait soit sa profondeur (ResNet), soit sa largeur (WideResNet), soit la résolution d'image. EfficientNet-B0 utilise une formule mathématique pour augmenter les trois simultanément de manière équilibrée. Le "B0" est la version de base avec ~5.3 millions de paramètres. Cette architecture est basée sur la "Neural Architecture Search" (NAS), optimisée pour maximiser le gain de précision par rapport au coût de calcul (Flops).

**42. Qu'est-ce qu'une convolution séparable en profondeur (Depthwise Separable) présente dans MBConv ?**
*R :* Une convolution classique 3x3 sur 64 canaux demande énormément de calculs. MBConv sépare cela en deux étapes : une convolution 3x3 sur chaque canal individuellement (Depthwise), puis une convolution 1x1 pour combiner les canaux (Pointwise). Cela réduit le coût computationnel par un facteur de 8 à 9 sans perte significative de qualité, permettant au modèle EquiVision d'être extrêmement rapide, même sur un simple processeur.

**43. Pourquoi la fonction Swish est-elle préférée à ReLU dans les modèles modernes ?**
*R :* ReLU coupe brutalement toutes les valeurs négatives à zéro, ce qui peut "tuer" certains neurones pendant l'entraînement. Swish ($x \cdot sigmoid(x)$) est une fonction lisse qui possède une petite courbure négative. Cela permet de conserver des gradients faibles mais non nuls pour les entrées négatives, facilitant ainsi l'optimisation et la capture de motifs subtils dans les images de chevaux.

**44. Comment avez-vous implémenté le Transfer Learning pour les 13 races ?**
*R :* Nous avons chargé les poids EfficientNet-B0 entraînés sur les 1.2 million d'images d'ImageNet. Nous avons ensuite "gelé" tous les poids du backbone (les couches qui extraient les formes) et remplacé la couche finale (1000 classes d'origine) par une "tête" personnalisée de 13 classes. L'idée est que le modèle sait déjà ce qu'est une oreille, un poil ou une jambe ; il n'a plus qu'à apprendre à combiner ces éléments pour distinguer un "Arabe" d'un "Barbe".

**45. Expliquez votre stratégie de Fine-Tuning progressif.**
*R :* L'entraînement s'est fait en deux phases. Phase 1 : Entraînement de la tête seule pendant 5-10 époques avec un Learning Rate élevé (1e-3). Phase 2 : Dégel des dernières couches du backbone et ré-entraînement avec un Learning Rate très faible (1e-5). Cela permet d'ajuster les filtres de haut niveau aux spécificités équines sans "oublier" les connaissances générales du modèle d'origine.

**46. Comment la `CrossEntropyLoss` gère-t-elle la probabilité de classe ?**
*R :* Elle combine une couche `LogSoftmax` et une `NLLLoss` (Negative Log Likelihood). Mathématiquement, elle pénalise de manière logarithmique le modèle s'il est très confiant dans une mauvaise réponse. Pour EquiVision, si le modèle hésite entre un Pur-sang Anglais et un Arabe (races proches), la CrossEntropy générera un gradient qui forcera le modèle à se concentrer sur les critères discriminants (comme la forme de la tête).

**47. Quel est l'intérêt de la Normalisation ImageNet (Mean/Std) ?**
*R :* Les images brutes ont des pixels entre 0 et 255. En soustrayant la moyenne et en divisant par l'écart-type d'ImageNet, on ramène les valeurs autour de zéro. Cela stabilise le calcul des gradients et évite les explosions numériques dans les couches profondes du réseau de neurones.

**48. Détaillez votre pipeline de "Data Augmentation".**
*R :* Pour rendre le modèle robuste aux photos prises par les utilisateurs, nous appliquons : `RandomResizedCrop` (simulation de zoom), `HorizontalFlip` (symétrie), `ColorJitter` (variation d'éclairage et de contraste) et `RandomRotation`. Cela multiplie virtuellement la taille du dataset et empêche le modèle de mémoriser des détails inutiles comme l'arrière-plan du box.

**49. Pourquoi la résolution 224x224 est-elle un compromis idéal ?**
*R :* Une résolution plus haute (ex: 600x600) capturerait plus de détails mais augmenterait le temps de calcul de manière quadratique ($N^2$). À 224x224, EfficientNet-B0 conserve son efficacité structurelle. Les détails critiques pour identifier les races (oreilles, profil de tête, membres) restent parfaitement visibles à cette échelle.

**50. Qu'est-ce que le Global Average Pooling (GAP) ?**
*R :* Au lieu d'utiliser des couches `Flatten` qui créent des millions de paramètres et risquent l'overfitting, le GAP prend la moyenne de chaque carte de caractéristiques finale. Si nous avons 1280 filtres, le GAP produit un vecteur de 1280 valeurs. C'est plus robuste et cela permet au modèle d'être invariant aux translations (le cheval peut être n'importe où dans l'image).

*(Questions 51-90 : Détails sur le Learning Rate Warmup, Weight Decay, Batch Normalization layers, Gradient Clipping, Top-k accuracy evaluation logic...)*

---

## 💰 PARTIE 3 : Machine Learning & Pricing (91-140)

**91. Pourquoi utiliser un Stacking Regressor plutôt qu'un seul modèle XGBoost ou Random Forest ?**
*R :* Le Stacking est une méthode d'ensemble de "niveau 2". Chaque modèle de base (Random Forest, HistGradientBoosting, XGBoost) a ses propres forces et faiblesses structurelles. Par exemple, Random Forest est excellent pour la stabilité, tandis que XGBoost capture mieux les relations complexes. Le Stacking utilise un "Meta-Learner" (un modèle final) qui apprend à quel point il doit faire confiance à chaque sous-modèle selon les caractéristiques du cheval. Cette approche réduit significativement l'erreur de généralisation et rend le système de pricing d'EquiVision beaucoup plus résilient aux anomalies de données.

**92. Expliquez le fonctionnement du meta-learner (Ridge Regression) et l'importance de la régularisation L2.**
*R :* Le meta-learner combine les sorties des modèles de base. Nous avons choisi la régularisation Ridge (L2) car elle ajoute une pénalité au carré des coefficients. Cela empêche le meta-learner de devenir trop dépendant d'un seul modèle de base (phénomène d'overfitting). En contraignant les poids, le Ridge assure que la prédiction finale est une moyenne pondérée intelligente et stable, garantissant que même si un modèle de base donne une valeur aberrante, le meta-learner saura la tempérer.

**93. Qu'est-ce que le "Target Leakage" (Fuite de cible) et comment l'avez-vous évité ?**
*R :* La fuite de cible survient lorsque des données qui ne seraient pas disponibles lors d'une prédiction réelle sont injectées dans l'entraînement. Dans notre cas, nous avons veillé à ne jamais inclure de statistiques post-vente (ex: date de transaction réelle ou prix final de vente remisé) dans les caractéristiques d'entrée. Tout le preprocessing (mise à l'échelle, encodage) est calculé sur le set d'entraînement uniquement, puis appliqué au set de test, évitant ainsi que le modèle "divine" le prix à partir de la distribution globale.

**94. Pourquoi prédire le logarithme du prix (`log1p`) plutôt que le prix brut ?**
*R :* Les prix des chevaux ne suivent pas une loi normale ; ils ont une distribution asymétrique (Skewed) avec une longue traîne vers les prix très élevés (Pur-sang de luxe). Les algorithmes de régression (MSE) sont très sensibles aux grandes valeurs. En utilisant `log1p(x) = log(1+x)`, nous transformons cette échelle exponentielle en échelle linéaire. Cela améliore la stabilité numérique de l'entraînement et permet au modèle d'être aussi précis sur des chevaux à 10 000 DH que sur des chevaux à 100 000 DH, car l'erreur est alors minimisée en termes de pourcentage relatif.

**95. Détaillez la logique mathématique derrière vos "Caractéristiques Synthétiques" (ex: Score de Santé).**
*R :* Les données brutes d'annonces web sont souvent incomplètes. Nous avons créé des générateurs de bruit gaussien centrés sur des moyennes métier. Par exemple, pour le "Score de Santé", nous injectons une valeur aléatoire issue d'une distribution normale $\mathcal{N}(\mu, \sigma)$ où $\mu$ dépend de l'âge du cheval. Cette technique, appelée "Data Imputation avec Bruit", force le modèle à apprendre que le prix ne dépend pas seulement de la race, mais aussi d'un facteur d'incertitude biologique réaliste, simulant ainsi les variables non-observées par le scraping.

**96. Expliquez l'implémentation de la "Courbe de Valeur de l'Âge" (Gaussienne centrée sur 6.5 ans).**
*R :* Un cheval n'a pas une valeur linéaire par rapport à son âge. Sa valeur culmine vers 6-7 ans (maturité sportive) et décline après 12-15 ans. Nous avons modélisé cela via une fonction gaussienne : $V(age) = \exp(-\frac{(age - 6.5)^2}{2\sigma^2})$. En injectant ce score comme feature, nous donnons au modèle de Machine Learning une "connaissance métier" explicite du cycle de vie équin, ce qu'un modèle pur aurait mis beaucoup plus de temps à déduire des données brutes bruitées.

**97. Comment gérez-vous l'imputation des données manquantes (NaN) dans le pipeline ?**
*R :* Nous utilisons le `SimpleImputer` au sein d'un `ColumnTransformer`. Pour les variables numériques comme la taille, nous imputons par la médiane calculée sur le set d'entraînement (plus robuste que la moyenne face aux erreurs de saisie). Pour les variables catégorielles (ex: Ville), nous créons une nouvelle modalité "Missing". Cela permet de garder le modèle opérationnel même si l'utilisateur ne remplit que 50% du formulaire de prédiction.

**98. Pourquoi privilégier le "One-Hot Encoding" pour la variable "Race" ?**
*R :* Les modèles linéaires supposent une relation d'ordre si nous utilisons des chiffres (1, 2, 3). Le One-Hot crée une colonne binaire par race, supprimant tout biais d'ordre artificiel. Pour EquiVision, cela permet au modèle de traiter chaque race comme une entité distincte avec son propre impact de "luxe" sur le prix final.

**99. Quel est l'impact du `StandardScaler` sur les modèles sensibles à l'échelle ?**
*R :* Les modèles comme Ridge ou SVR utilisent des calculs de distance. Si la "Taille" est en cm (160) et l'"Âge" en années (5), le modèle donnerait trop d'importance à la taille par défaut. Le `StandardScaler` ramène chaque variable à une moyenne de 0 et un écart-type de 1, mettant toutes les caractéristiques sur un pied d'égalité mathématique pour l'optimiseur.

**100. Quelle est la différence entre RMSE et MAE pour l'évaluation du prix ?**
*R :* Le MAE (Mean Absolute Error) est l'erreur brute en DH (ex: 500 DH d'erreur en moyenne). Le RMSE (Root Mean Squared Error) pénalise plus lourdement les grandes erreurs (le carré de l'erreur). Nous utilisons le RMSE pour l'entraînement (pour éviter les prédictions absurdes) mais nous présentons le MAE au jury car il est beaucoup plus facile à vulgariser.

*(Questions 101-140 : Détails sur le Feature Selection via Lasso, importance des résidus, validation croisée imbriquée (Nested CV), gestion des outliers par l'IQR, etc...)*

---

## ⚙️ PARTIE 4 : MLOps & Orchestration (141-180)

**141. Pourquoi avoir compartimenté le projet en plusieurs services avec Docker Compose ?**
*R :* L'isolation par conteneurs permet de garantir la reproductibilité totale de l'environnement, peu importe la machine hôte. Dans EquiVision, le backend (FastAPI/PyTorch) a des dépendances lourdes qui pourraient entrer en conflit avec Airflow ou MLflow. Docker Compose orchestre ces services dans un réseau virtuel privé, permettant une communication sécurisée via les noms de services (ex: `http://backend:8000`). C'est une architecture micro-services standard qui facilite la mise à l'échelle (scaling) globale du projet.

**142. Expliquez le cycle de vie d'un DAG Airflow pour le ré-entraînement du modèle.**
*R :* Un Directed Acyclic Graph (DAG) chez nous orchestre le pipeline de données. Il commence par un `ScrapingOperator` (extraction des prix actualisés), suivi d'un `ProcessingOperator` (nettoyage Pandas). Une fois les données prêtes, le `TrainingOperator` lance l'apprentissage de l'ensemble Stacking et enregistre les résultats dans MLflow. Si les métriques sont validées, le modèle est marqué comme "Production" et le backend le charge automatiquement. Ce degré d'automatisation est ce qui transforme un simple script ML en un produit MLOps industriel.

**143. Comment MLflow transforme-t-il votre approche de "Data Scientist" ?**
*R :* Avant MLflow, nous devions noter manuellement les performances de chaque test. Désormais, chaque entraînement est un "Run" tracé. Nous pouvons comparer visuellement les courbes de convergence de EfficientNet ou les résidus de notre Stacking Regressor. Le "Model Registry" nous permet de versionner nos modèles comme on versionne du code avec Git, assurant une traçabilité totale : on sait exactement quelles données et quels hyperparamètres ont produit le modèle actuellement en ligne.

**144. Détaillez le passage de données via Airflow XComs et ses limites.**
*R :* Les XCom (Cross-Communications) permettent de passer des messages entre tâches. Nous les utilisons pour transmettre les chemins des fichiers CSV générés ou les IDs des runs MLflow. Cependant, les XCom sont stockés dans la base de données d'Airflow ; nous évitons donc d'y passer de gros volumes de données. Pour les DataFrames volumineux, nous passons par le stockage disque persistant (Volumes Docker) et n'utilisons XCom que pour transmettre le "pointeur" (le chemin du fichier).

**145. Qu'est-ce qu'un "Multi-stage Build" dans vos Dockerfiles ?**
*R :* Pour le backend, nous utilisons une première étape (stage) pour installer les dépendances et compiler certains modules, puis une seconde étape "légère" qui ne contient que le runtime Python et le code. Cela permet de réduire la taille de l'image Docker de 2 Go à quelques centaines de Mo, accélérant drastiquement le déploiement et renforçant la sécurité en éliminant les outils de build inutiles en production.

*(Questions 146-180 : Détails sur les réseaux Docker Bridge, la persistance PostgreSQL via volumes, la configuration du Scheduler Airflow, les Artifacts MLflow, etc...)*

---

## 📊 PARTIE 5 : Évaluation, Data & Logique (181-200)

**181. Qu'est-ce que le R² (Coefficient de détermination) et pourquoi est-il crucial pour le pricing ?**
*R :* Le R² indique le pourcentage de la variation du prix qui est expliqué par notre modèle. Un score de 0.85 est excellent pour du pricing réel. Si nous avions un R² de 1.0 (ou très proche), cela indiquerait un Overfitting massif ou, pire, un Target Leakage (fuite de données). Dans le monde réel des chevaux, le prix comporte une part d'irrationalité émotionnelle que l'IA ne peut pas (et ne doit pas) prédire parfaitement.

**182. Comment gérez-vous le "Model Drift" (dérive du modèle) au fil du temps ?**
*R :* Le marché du cheval fluctue. Les prix scrapés aujourd'hui ne seront plus valables dans un an. Notre pipeline Airflow inclut une étape de "Monitoring" qui compare les prédictions aux nouveaux prix réels. Si l'erreur moyenne (MAE) augmente au-delà d'un seuil critique, le DAG déclenche automatiquement une alerte et un ré-entraînement sur les données les plus récentes pour "recadrer" l'intelligence du modèle.

**183. Quelle est la limite principale de votre système actuel et comment la dépasser ?**
*R :* La limite est la qualité des descriptions textuelles sur le web. Si un vendeur écrit mal sa ville ou oublie de préciser l'âge, l'IA perd en précision. Une évolution majeure serait d'intégrer du NLP (Natural Language Processing) plus poussé via des modèles comme RoBERTa pour extraire des informations sémantiques riches (ex: "cheval de concours", "idéal débutant") et les transformer en caractéristiques numériques.

**184-200. (Perspectives d'avenir : Analyse vidéo de la démarche, intégration de la généalogie, scalabilité horizontale, conclusion sur l'impact métier d'EquiVision).**
