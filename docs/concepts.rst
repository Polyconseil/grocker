Qu'est que Grocker ?
====================

**Grocker** est une chaîne de construction permettant à partir d'un nom d'application et de la version de celle-ci de
créer une image *Docker* contenant l'ensemble des briques logicielles (hors services externes) nécessaires à l'exécution
du code de cette application.

Comment est construite l'image ?
================================

Grocker construit l'image en trois temps :

 - Dans une première phase, il compile l'application, le point d'entrée et leurs dépendances (par exemple, il crée des
   *wheel* pour les projets *Python*). Pour cela une image contenant les dépendances de construction est utilisée.
   Le résultat de la compilation est enregistré dans un data volume, géré par docker, utilisé comme un cache.

 - Dans une seconde phase, un serveur web est lancé pour servir le résultat de la compilation.

 - Dans la dernière phase, il installe les résultats de la compilation sur une image propre (i.e. sans les dépendances
   de construction). L'application doit fournir un point point d'entrée nommé ``grocker-runner`` pour permettre de
   simplifier son lancement.

.. graphviz::

    strict digraph builder {
        labeljust=l;
        compound=true;
        rankdir=LR;

        node [shape="box"];


        subgraph cluster_BASE {
            label="Base Image";

            BASE [shape=point, label="", color=none];

            BASE_SYS [label="System Base Image", color=grey];
            BASE_DEP [label="Base Dependencies", shape=egg];
        }

        subgraph cluster_CMP {
            label="Compiler";

            CMP_BASE [label="Base Image", color=grey];
            CMP [shape=point, label="", color=none];
            CMP_BUILD [label="Build Dependencies", shape=egg];

        }

        subgraph cluster_WHEEL_STORAGE {
            label = "Data volume for wheels";

            subgraph PKG {
                node [label=pkg, shape=box3d, color=darkcyan];

                PKG_1
                PKG_2
                PKG_3
            }

        }

        subgraph WEB_SERVER {
            WEB_SERVER [label="Web server", color=grey];
        }

        subgraph cluster_RUN {
            label="Runner";

            RUN_BASE [label="Base Image", color=grey];
            RUN_RUNNER [label="Application Dependencies", shape=egg];
        }

        BASE -> {RUN_BASE, CMP_BASE} [ltail=cluster_BASE, color=grey];
        CMP -> {PKG_1, PKG_2, PKG_3} [ltail=cluster_CMP, color=darkcyan];
        {PKG_1, PKG_2, PKG_3} -> WEB_SERVER [color="darkcyan"];
        WEB_SERVER -> RUN_RUNNER [ltail=WEB_SERVER, color=darkcyan];

        RUN_RUNNER [color=darkcyan];

    }

Grocker construit trois images *Docker*, dont les deux premières sont réutilisées entre les constructions :

 1. L'**image de base** contient les dépendances systèmes nécessaires aux deux autres images et le *runtime* utilisé.

 #. L'**image de compilation** (*compiler*) est l'image de base augmentée des dépendances de construction et d'un
    script décrivant comment doivent être compilés les projets en fonction de leur langage de programmation. Cette image
    exporte dans un dossier sur la machine hôte le résultat de la compilation.

 #. L'**image finale** (*runner*) est le produit final de la chaîne de construction *Grocker*. Elle contient
    l'application et ses dépendances (hors services externes).
