"""
Contenido estático del CV.

Se mantiene en Python (no DB) porque:
    - El esquema solicitado solo cubre users/projects.
    - Para un portafolio personal con un único dueño, editar aquí + PR es más
      rápido que construir UIs de administración para cada sección del CV.
    - Versionado en git = historial auditable de cambios al CV.

Si en el futuro Luis quiere gestionar esto por UI, migrar a tablas es directo.
Todos los strings se renderizan con autoescape de Jinja activo (nunca |safe).
"""

CV = {
    "profile": {
        "name": "Luis Eduardo De la Espriella Jiménez",
        "role": "Contador Público · Consultor Financiero · Perfil Tecnológico",
        "location": "Colombia",
        "email": "luisdelaespriellaj@hotmail.com",
        "instagram": "@ledelaespriella",
        "summary": (
            "Contador Público colombiano con vocación por la tecnología. "
            "Acompaño a organizaciones en auditoría, tributación y finanzas "
            "apoyándome en herramientas digitales e inteligencia artificial "
            "para entregar análisis rigurosos, oportunos y accionables."
        ),
    },
    "about": [
        "Más de una década combinando rigor contable con automatización y análisis de datos.",
        "Experiencia trabajando con equipos técnicos y de negocio para traducir requisitos financieros en soluciones operativas.",
        "Aprendizaje continuo: desarrollo de software, ciencia de datos y aplicaciones de IA al dominio contable.",
    ],
    "experience": [
        {
            "role": "Consultor Financiero y Contable",
            "company": "Práctica independiente",
            "period": "Actualidad",
            "highlights": [
                "Auditoría financiera y tributaria para PYMEs.",
                "Diseño de procesos y controles internos.",
                "Automatización de reportes financieros con Python y hojas de cálculo avanzadas.",
            ],
        },
        {
            "role": "Contador Público",
            "company": "Experiencia corporativa",
            "period": "Trayectoria previa",
            "highlights": [
                "Cierres contables mensuales y anuales.",
                "Preparación de declaraciones tributarias.",
                "Colaboración con áreas de TI en la implantación de sistemas ERP.",
            ],
        },
    ],
    "skills": [
        {"group": "Contables", "items": ["Auditoría", "Tributación", "NIIF", "Control interno", "Análisis financiero"]},
        {"group": "Tecnología", "items": ["Python", "SQL", "Excel avanzado", "Power BI", "Automatización"]},
        {"group": "IA y datos", "items": ["Análisis de datos", "Modelos LLM aplicados", "Prompting estructurado"]},
        {"group": "Soft skills", "items": ["Comunicación con stakeholders", "Pensamiento crítico", "Ética profesional"]},
    ],
    "education": [
        {
            "degree": "Contador Público",
            "institution": "Universidad (Colombia)",
            "period": "",
            "detail": "Formación profesional en contabilidad, auditoría y tributación.",
        },
    ],
    "contact": {
        "email": "luisdelaespriellaj@hotmail.com",
        "instagram_url": "https://instagram.com/ledelaespriella",
        "note": "Escríbeme por correo o Instagram para consultas profesionales.",
    },
}
