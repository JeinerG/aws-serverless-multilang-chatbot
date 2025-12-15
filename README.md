# aws-serverless-multilang-chatbot: Chatbot Inteligente con NLP y Machine Learning (AWS)

## Descripción del Proyecto
Este proyecto consiste en el desarrollo de un chatbot conversacional inteligente integrado en una interfaz web. Utiliza servicios avanzados de Procesamiento de Lenguaje Natural (NLP) y Machine Learning de Amazon Web Services (AWS) para ofrecer una experiencia de usuario interactiva y eficiente.

El sistema no solo responde preguntas, sino que también es capaz de analizar el sentimiento del usuario y comunicarse en múltiples idiomas, sirviendo como una solución robusta para atención al cliente y soporte automatizado.

## Arquitectura de la Solución
La arquitectura está diseñada para ser *serverless*, garantizando escalabilidad y alta disponibilidad.

![Arquitectura del Flujo](architecture_flow.jpeg)

### Flujo de Datos
1.  **Frontend**: Los usuarios interactúan a través de una interfaz web alojada en **Amazon S3** y distribuida globalmente mediante **Amazon CloudFront**.
2.  **API Gateway**: Actúa como el punto de entrada seguro, manejando las conexiones (posiblemente vía WebSocket) hacia el backend.
3.  **Lambda (Orquestador)**: Una función AWS Lambda recibe las solicitudes y orquesta el flujo hacia el motor conversacional.
4.  **Amazon Lex**: Es el núcleo del chatbot. Procesa el lenguaje natural (NLU), identifica la intención del usuario (Intents) y extrae información relevante (Slots).
5.  **Lambda (Fulfillment)**: Ejecuta la lógica de negocio necesaria para cumplir con la solicitud del usuario.
6.  **Servicios Cognitivos y de Datos**:
    *   **Amazon DynamoDB**: Base de conocimientos utilizada para recuperar respuestas dinámicas o almacenar el contexto de la sesión.
    *   **Amazon Comprehend**: Analiza el sentimiento de la entrada del usuario para ajustar el tono de la respuesta.
    *   **Amazon Translate**: Permite la traducción automática en tiempo real para soporte multi-idioma (Español, Inglés, Portugués).

## Stack Tecnológico (Servicios AWS)
*   **Amazon Lex**: Motor conversacional (NLU/ASR).
*   **AWS Lambda**: Computación serverless para lógica de negocio y orquestación.
*   **Amazon Comprehend**: Análisis de sentimiento.
*   **Amazon Translate**: Traducción neuronal de idiomas.
*   **Amazon DynamoDB**: Base de datos NoSQL para persistencia de datos y KB.
*   **Amazon API Gateway**: Gestión de APIs y WebSockets.
*   **Amazon S3**: Almacenamiento de activos estáticos del frontend.
*   **Amazon CloudFront**: CDN para entrega rápida de contenido.

## Funcionalidades Clave
*   **Soporte Multi-idioma**: Capacidad para interactuar fluidamente en Español, Inglés y Portugués.
*   **Análisis de Sentimiento**: Detección del estado emocional del usuario en cada interacción para mejorar la calidad del servicio.
*   **Gestión de Contexto**: Memoria de sesión para mantener conversaciones coherentes.
*   **Intenciones Complejas**: Soporte para más de 5 intents con validaciones personalizadas en los slots.
*   **Base de Conocimiento Dinámica**: Integración con DynamoDB para respuestas actualizables sin redesplegar el bot.
*   **Fallback Inteligente**: Manejo elegante de consultas no reconocidas.

## Desafíos Técnicos Superados
*   Implementación de memoria de sesión (contexto conversacional) en un entorno stateless.
*   Orquestación de múltiples servicios cognitivos (Lex, Comprehend, Translate) con baja latencia.
*   Diseño de una interfaz web responsiva e integrada.

---
*Este proyecto demuestra la integración efectiva de servicios managed de AWS para crear soluciones de IA conversacional modernas y escalables.*

