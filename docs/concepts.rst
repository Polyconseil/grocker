Qu'est que Grocker ?
====================

**Grocker** est une chaîne de construction permettant à partir d'un nom d'application et de la version de celle-ci de
créer une image *Docker* contenant l'ensemble des briques logicielles (hors services externes) nécessaires à l'exécution
du code de cette application.

.. graphviz::

   strict digraph containerized_app {
        node [shape="box"];

        LB [label="Load Balancer"];

        subgraph cluster_VM {
            label="VM";
            labeljust=l;

            VM_RP [label="Nginx", margin="1,0.1"];

            subgraph cluster_CNT {
                label="Container";

                CNT_RP [label="Nginx\n(only for service instances)", margin="1,0.1"];
                CNT_UWSGI [label="Uwsgi\n(only for service instances)", margin="1,0.1"];
                CNT_SMTPD [label="Simple SMTP Relay\n(not a daemon)", margin="1,0.1", shape=cds];

                subgraph cluster_APP {
                    label="Application";

                    APP [label="App code"];
                    APP_STATIC [label="Statics", shape=folder];
                }

                CNT_CRON [label="Con Daemon\n(only for cron instance)"];
                CNT_MEDIA [label="Media", shape=folder, color=grey];
                CNT_DEV_LOG [label="/dev/log", shape=note, color=grey];
                CNT_CONFIG [label="/config", shape=folder, color=grey];
                CNT_SCRIPTS [label="/scripts", shape=folder, color=grey];
            }

            VM_MEDIA [label="Media", shape=folder, color=grey];
            VM_DEV_LOG [label="/dev/log", shape=note];
            VM_CONFIG [label="/config", shape=folder];
            VM_SCRIPTS [label="/scripts", shape=folder];
            VM_SMTPD [label="SMTP Relay", margin="1,0.1", shape=cds];
        }

        subgraph external {
            KBR [label="Kerberos", shape=septagon];
            REDIS [label="Redis", shape=doubleoctagon];
            DB [label="Postgres", shape=doubleoctagon];
            NFS [Label="NFS Server", shape=folder];
            EXT_WS [label="External WebServices", shape=egg];
            SMTP [label="SMTP Server",  margin="1,0.1", shape=cds];

            EXT_WS -> DB -> REDIS [style=invis];  # only to improve representation
        }

        LB -> VM_RP [dir="both"];

        VM_RP -> KBR [dir="both"];
        VM_RP -> CNT_RP [dir="both"];

        CNT_RP -> CNT_UWSGI [dir="both"];
        CNT_UWSGI -> APP [dir="both"];
        CNT_RP -> APP_STATIC [dir="both", color=darkcyan];
        CNT_RP -> CNT_MEDIA [dir="both", label="X-Accel-Redirect", color=darkcyan, fontcolor=darkcyan];

        CNT_CRON -> APP [rank=same];
        {CNT_CRON, APP} -> CNT_SMTPD -> VM_SMTPD -> SMTP;
        APP -> REDIS [dir="both"];
        APP -> DB [dir="both"];
        APP -> EXT_WS [dir="both"];
        APP -> CNT_MEDIA [dir="both"];

        NFS -> VM_MEDIA -> CNT_MEDIA [arrowtail=inv, dir=both, color=grey];
        VM_DEV_LOG -> CNT_DEV_LOG [arrowtail=inv, dir=both, color=grey];
        VM_CONFIG -> CNT_CONFIG [arrowtail=inv, dir=both, color=grey];
        VM_SCRIPTS -> CNT_SCRIPTS [arrowtail=inv, dir=both, color=grey];
   }


Comment est construite l'image ?
================================

Grocker construit l'image en deux temps :

 - Dans une première phase, il compile l'application et ses dépendances (par exemple, il crée des *wheel* pour les
   projets *Python*). Pour cela une image contenant les dépendances de construction est utilisée.

 - Dans la seconde phase, il installe les résultats de la compilation sur une image propre (i.e. sans les dépendances
   de construction). Le point d'entrée de cette image permet de lancer soit le service *cron*, soit un service fourni
   par l'application (``ops``, ``www``, ``ws``, *etc*), soit une commande (*shell*, script ou autre).


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

        subgraph PKG {
            node [label=pkg, shape=box3d, color=darkcyan];

            PKG_1
            PKG_2
            PKG_3
        }

        subgraph cluster_RUN {
            label="Runner";

            RUN_BASE [label="Base Image", color=grey];
            RUN_RUNNER [label="Application Dependencies", shape=egg];
        }

        BASE -> {RUN_BASE, CMP_BASE} [ltail=cluster_BASE, color=grey];
        CMP -> {PKG_1, PKG_2, PKG_3} [ltail=cluster_CMP, color=darkcyan];
        {PKG_1, PKG_2, PKG_3} -> RUN_RUNNER [color=darkcyan];

    }

Grocker construit trois images *Docker*, dont les deux premières sont réutilisées entre les constructions :

 1. L'**image de base** contient les dépendances systèmes nécessaires aux deux autres images. Elle contient entre
    autres:

    - Un *reverse proxy* (*Nginx*) ;
    - *Python* (2 et 3) et les versions *Uwsgi* associées ;
    - les bibliothèques d'accès aux bases de données (*libpq*) ;
    - les bibliothèques de manipulation d'images.

 #. L'**image de compilation** (*compiler*) est l'image de base augmentée des dépendances de construction et d'un
    script décrivant comment doivent être compilés les projets en fonction de leur langage de programmation. Cette image
    exporte dans un dossier sur la machine hôte le résultat de la compilation.

 #. L'**image finale** (*runner*) est le produit final de la chaîne de construction *Grocker*. Elle contient
    l'application et ses dépendances (hors services externes) et un point d'entrée permettant de lancer facilement les
    différents services de l'application.
