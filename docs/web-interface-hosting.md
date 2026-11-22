# Ideas para una interfaz web y su alojamiento

Estas son opciones para evolucionar la interfaz actual de Streamlit; no son decisiones definitivas.

## Interfaz con TypeScript y Vite

Una interfaz en JavaScript o TypeScript permitiría crear controles, animaciones y una presentación del mapa más personalizados. El motor actual, incluidas las reglas de movimiento y eventos, está escrito en Python.

Vite es una herramienta para desarrollar y preparar aplicaciones web: ofrece un servidor local de desarrollo y genera los archivos HTML, CSS y JavaScript para publicar. No es un servicio de alojamiento ni exige usar React.

## Opciones de arquitectura

### Motor en el navegador

Reescribir el motor en TypeScript permitiría ejecutar el juego en el navegador y publicar la aplicación estática en [GitHub Pages](https://docs.github.com/pages/getting-started-with-github-pages/github-pages-limits) o [Cloudflare Pages](https://developers.cloudflare.com/pages/platform/limits/). Esto simplifica el alojamiento, pero implica trasladar y mantener la lógica existente.

### Motor Python con API

Mantener el motor Python y añadir una API permite reutilizar las reglas actuales:

```text
Interfaz TypeScript en GitHub Pages
              |
              v
API Python en Render
              |
              v
Gemini, para la narración
```

GitHub Pages sirve archivos estáticos y no ejecuta Python. [Render](https://render.com/docs/free) ofrece servicios web gratuitos aptos para una API Python, sujetos a límites: el servicio se duerme tras 15 minutos sin tráfico y puede tardar aproximadamente un minuto en despertar. Las condiciones y cuotas de los servicios pueden cambiar.

Esta combinación es una posible primera opción para mejorar la interfaz sin reescribir todo el juego. La API y la interfaz estarían en orígenes distintos, por lo que habría que configurar CORS. Las partidas que deban sobrevivir a reinicios necesitarían almacenamiento persistente.

## Protección de la clave de Gemini

La clave privada no debe incluirse en el código de la interfaz, el repositorio ni los archivos publicados en GitHub Pages. Tampoco debe usarse una variable `VITE_` para guardarla: sus valores quedan disponibles en el código del navegador.

En la arquitectura con API, la clave puede guardarse como variable de entorno `GEMINI_API_KEY` en el panel del servidor. Python la lee en el servidor y realiza la llamada a Gemini; el navegador recibe únicamente el resultado. Para desarrollo local se puede usar un archivo `.env`, excluido de Git mediante `.gitignore`.

Ocultar la clave no protege por sí solo una API pública contra el uso abusivo. Conviene añadir límites de uso y, según el caso, autenticación, además de vigilar cuotas y costes. CORS no sustituye estas medidas. El alojamiento gratuito tampoco implica que las llamadas a Gemini sean gratuitas. Si se publica una clave accidentalmente, hay que revocarla y crear otra.

Sin servidor, cada jugador podría introducir su propia clave en el navegador. Esa clave estaría disponible para el código ejecutado allí, por lo que esta opción no protege una clave compartida del proyecto.
