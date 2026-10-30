flowchart TD
    %% ===== Fuentes externas =====
    subgraph EXT["Fuentes externas"]
        GH["GitHub Projects v2"]
        MCPSRV["Servidor MCP Proyectos<br/>PROJECTS_MCP_URL, endpoint /mcp"]
        COPILOT["GitHub Copilot SDK<br/>modelo COPILOT_MODEL"]
        OASPEC["client/openapi<br/>contratos externos"]
    end

    %% ===== Orquestador =====
    subgraph ORQ["Orquestador main.py"]
        MAIN["main.py<br/>flujo HITL por etapa"]
        WF["crew/workflow.py<br/>ROLES y DATA_ROLES"]
        GUARD["guard_input<br/>anti prompt injection y redaccion de secretos"]
        CKPT[("output/.checkpoint.json")]
        HITL{{"Humano<br/>s aprobar, r reintentar, n abortar"}}
    end

    %% ===== Cliente MCP =====
    subgraph MCPC["Cliente MCP mcp_projects.py"]
        LP["list_projects"]
        LPI["list_project_items"]
        GF["get_feature_from_item"]
    end

    %% ===== LLM =====
    subgraph LLMS["Capa LLM"]
        CLLM["CopilotLLM<br/>crew/copilot_llm.py"]
        RT["lab_copilot/runtime.py<br/>streaming en terminal"]
    end

    %% ===== Agentes CrewAI =====
    subgraph AGENTS["Agentes CrewAI, en orden"]
        SP["1 specifier<br/>OpenSpec proposal y specs"]
        AR["2 architect<br/>load_issue, diagramas, OpenAPI, tareas"]
        DA["data<br/>opcional, CREWAI_INCLUDE_DATA"]
        BE["3 backend<br/>bucle de herramientas"]
        FE["4 frontend<br/>Angular"]
        TE["5 testing<br/>pytest API y Selenium E2E"]
        SE["6 security"]
        CH["7 chapter"]
    end

    %% ===== Herramientas del backend =====
    subgraph TOOLS["Herramientas del backend crew/dev_loop.py"]
        DL["run_dev_loop<br/>max 12 iteraciones"]
        FSTOOLS["write_file, read_file, list_files"]
        RUNTOOLS["run_pytest, run_ruff"]
        FIN["finish<br/>solo si pytest esta en verde"]
    end

    %% ===== Persistencia y validacion =====
    subgraph OUT["Entregables y validacion"]
        CHG["openspec/changes/feature/<br/>design.md, tasks.md, openapi.yaml, specs, reports"]
        CODE["openspec/changes/feature/code/backend<br/>app y tests"]
        OSCLI["OpenSpec CLI<br/>openspec validate"]
        GUARDOUT["check_output<br/>guardrails por rol"]
    end

    %% ===== Conexiones =====
    GH --> MCPSRV
    MCPSRV --> LP
    MCPSRV --> LPI
    MCPSRV --> GF
    MAIN -->|"elegir proyecto"| LP
    MAIN -->|"elegir item"| LPI
    MAIN --> GUARD
    GUARD --> AR
    AR -->|"load_issue"| GF

    MAIN --> WF
    WF --> SP
    WF --> AR
    WF --> DA
    WF --> BE
    WF --> FE
    WF --> TE
    WF --> SE
    WF --> CH

    SP -->|"run_role"| CLLM
    AR -->|"run_role"| CLLM
    DA -->|"run_role"| CLLM
    FE -->|"run_role"| CLLM
    TE -->|"run_role"| CLLM
    SE -->|"run_role"| CLLM
    CH -->|"run_role"| CLLM
    BE -->|"develop"| DL

    DL -->|"prompt y respuesta"| CLLM
    CLLM --> RT
    RT --> COPILOT
    AR -.->|"lee contratos"| OASPEC
    MAIN -.->|"read_openapi"| OASPEC

    DL --> FSTOOLS
    DL --> RUNTOOLS
    DL --> FIN
    FSTOOLS --> CODE
    RUNTOOLS -->|"python -m pytest y ruff"| CODE

    SP --> CHG
    AR --> CHG
    DA --> CHG
    FE --> CHG
    TE --> CHG
    SE --> CHG
    CH --> CHG
    BE --> CHG
    CHG --> GUARDOUT
    GUARDOUT --> OSCLI

    MAIN --> HITL
    HITL -->|"r feedback"| MAIN
    HITL -->|"s aprobado"| CKPT
    CKPT --> MAIN
    MAIN -->|"fin del flujo"| OSCLI