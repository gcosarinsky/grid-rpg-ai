# 🗺️ Proyecto: RPG Narrativo en Cuadrícula (Gemini/Gemma + Streamlit)

Este documento resume la arquitectura y lógica discutida para el desarrollo de un juego de rol basado en turnos, utilizando modelos de lenguaje (LLM) y una interfaz web dinámica.

---

## 🏗️ 1. Motor de Navegación (Lógica de Grilla)
- **Mapa:** Matriz de $6 \times 6$ con coordenadas $(x, y)$ iniciando en $(0,0)$ (arriba-izquierda).
- **Regiones:** Uso de valores numéricos para definir biomas:
  - `0`: Océano 🟦
  - `1`: Pradera 🟩
  - `2`: Montaña 🟫
  - `3`: Desierto 🟨
- **Sistema de Turnos:** Movimiento del jugador (manual) y de un NPC (controlado por IA) con detección de colisiones mediante comparación de vectores de posición.

## ☁️ 2. Infraestructura y Seguridad (Streamlit Cloud)
- **Gestión de Secretos:** Uso de `st.secrets` para ocultar la **API Key de Google**.
- **Configuración TOML:** Implementación de archivos `.streamlit/secrets.toml` para desarrollo local y configuración en el dashboard de Streamlit para producción.
- **Persistencia:** Uso de `st.session_state` para mantener el estado del mapa y el historial entre interacciones.

## 🧠 3. Cerebro Narrativo y Memoria
- **Modelo Sugerido:** Gemma 2 (Ventana de contexto de **8K tokens**).
- **Estrategia RAG (Retrieval-Augmented Generation):**
  - Implementación de una **Base de Datos Vectorial** (ChromaDB o FAISS).
  - En lugar de enviar todo el historial (lo que saturaría el contexto), se recuperan solo los "recuerdos" relevantes al turno actual.
- **Narrativa Dinámica:** El LLM actúa como Dungeon Master, reaccionando a la región actual y a la acción escrita por el usuario en cada turno.

## 📝 4. Optimización de Prompts
- **System Prompt:** Configurado para respuestas breves (máximo 3 frases) y tono oscuro/minimalista.
- **Prompt Dinámico:** Inyección de variables de entorno (Coordenadas + Bioma + Memoria + Acción) para garantizar coherencia sin desperdiciar tokens.

---
*Resumen generado para el flujo de trabajo del proyecto "Grid-RPG AI".*