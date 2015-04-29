Sécurité
========

L'image *Grocker* doit être utilisée derrière un *reverse proxy* qui doit nettoyer (ces en-têtes ne doivent pas venir
directement du client) les en-têtes *HTTP* suivants:

 - ``REMOTE_ADDR``
 - ``REMOTE_USER``
 - ``X-Accel-Redirect``
 - ``X-Forwarded-For``
 - ``X-Forwarded-Host``
 - ``X-Forwarded-Proto``
 - ``X-Real-IP``
 - ``X-Real-Scheme``

