# CHOMS-HOMELAB - Traefik + Authelia Final Status

## Estado

Traefik y Authelia quedan como capa principal de entrada del homelab.

## Público

- https://chomsmaster.com
- https://www.chomsmaster.com

## Protegido por Authelia

- https://home.chomsmaster.com
- https://grafana.chomsmaster.com
- https://kuma.chomsmaster.com
- https://traefik.chomsmaster.com

## Login propio

- https://auth.chomsmaster.com
- https://cloud.chomsmaster.com
- https://jellyfin.chomsmaster.com

## Operación

Usar siempre:

```bash
choms compose ps
choms compose up -d
choms compose logs traefik --tail=100
choms compose restart authelia
choms compose restart traefik

clear




