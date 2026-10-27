# O site ja e HTML/CSS/JS pronto: nao ha etapa de build, so copiar pro nginx.
# O contexto e a raiz do repo (ver build-image.sh), por isso os caminhos deploy/ e site/.
FROM nginx:alpine

COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY site/ /usr/share/nginx/html

# Sem cloudflare_ruleset neste stack (a fase de cache da zona e do
# tf-parque-palmeiras), entao o Cloudflare pode segurar styles.css/data.js/app.js
# antigos. Cada um ganha ?v=<md5> no index.html: conteudo novo, URL nova.
RUN cd /usr/share/nginx/html \
 && for f in styles.css data.js app.js; do \
      v=$(md5sum "$f" | cut -c1-8); \
      sed -i -E "s#(href|src)=\"$f\"#\1=\"$f?v=$v\"#" index.html; \
    done

EXPOSE 80
