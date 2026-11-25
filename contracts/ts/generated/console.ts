export interface paths {
    "/auth/login": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["login"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/logout": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["logout"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/auth/me": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["get_me"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/users": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["list_users"];
        put?: never;
        post: operations["create_user"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/users/{user_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch: operations["update_user"];
        trace?: never;
    };
    "/notice": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** @description Pública: solo devuelve el texto versionado del aviso de VE-01, para que se vea también al iniciar sesión (AC15.5.1; D-1, FD-U4-08; lista pública de NFRD-U1-12) */
        get: operations["get_notice"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/profiles": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["list_profiles"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["list_sessions"];
        put?: never;
        /** @description Sesión guiada. Exige consentimiento y un perfil aprobado; un perfil con proveedor comercial sin autoriza_transferencia da 422 profile.transfer_not_authorized antes de crear filas. */
        post: operations["create_session"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/import": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** @description Importa una transcripción en el formato de entrada de C6 con su bloque `consentimiento`. Sin el bloque se rechaza completa (salvo origen sintetico). El archivo debe cumplir C6 completo: `modo` debe ser `final` (si no, `import.invalid_transcript`) y `perfil` debe ser igual a `profile_name` del formulario (si no, `422` `import.profile_mismatch`); `hasta_turno` y `desde_turno`, si vienen, se ignoran. La sesión nace cerrada a turnos nuevos (FR3.6) y sus corridas son siempre de modo final, que se puede lanzar enseguida. El archivo es solo JSON; otro tipo responde 415 `import.invalid_type` (FD-U6-03). No lleva `client_request_id`: un doble envío crea dos sesiones, límite declarado, y M7 deshabilita «Importar» mientras crea (FD-U6-23). */
        post: operations["import_session"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** @description Sondeo de la consola. Con `since` devuelve solo lo que cambió desde ese cursor. Cada llamada del dueño con la sesión abierta cuenta como latido (AC7.1.1). Registra el acceso (C23) solo sin `since` (FD-U3-05). */
        get: operations["get_session"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/heartbeat": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["heartbeat_session"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/turns": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** @description Un turno escrito; encola una corrida incremental con desde_turno = hasta_turno = n (FR4.9), salvo con el análisis en pausa. */
        post: operations["create_turn"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/transcript": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** @description Bloque pegado, dividido en turnos con la especificación versionada (FR3.3); una sola corrida desde su primer turno. */
        post: operations["paste_transcript"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/final-runs": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** @description Lanza (o relanza) el modo final sobre toda la transcripción. Cuenta el último lanzado. De dos lanzamientos simultáneos, uno recibe 202 y el otro 409 run.final_in_progress. */
        post: operations["launch_final_run"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/runs/{run_id}/retry": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["retry_run"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/runs/{run_id}/model-calls": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["list_model_calls"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/analysis": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** @description Pausar o reanudar el análisis. Con `paused` en true la sesión pasa de `open` a `paused`, y con false vuelve a `open`, con actor y hora (SessionStatusChange); desde cualquier otro estado responde 409. En pausa los turnos se guardan sin encolar y las corridas en cola se cancelan sin llamar a modelos (DD-06). «Reanudar análisis» encola una corrida, así que la ruta responde `202` con `SessionView` como única 2xx, en las dos direcciones (C-3, NFR-U6-03, NFRD-U6-02). */
        patch: operations["set_analysis_paused"];
        trace?: never;
    };
    "/sessions/{session_id}/terminate": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** @description Terminar sesión. Cancela lo encolado y cierra la sesión a turnos nuevos; se puede consolidar después. */
        post: operations["terminate_session"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/consent-withdrawal": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** @description Registra la retirada del consentimiento con actor y hora (AC15.2.3). Desde ese momento no se encola ni se analiza ninguna corrida (VE-10 (a)). */
        post: operations["withdraw_consent"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/resume": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["resume_session"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/finalize": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["finalize_session"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/suggestions/{suggestion_id}/observation-views": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["view_observations"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/suggestions/{suggestion_id}/decisions": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["decide_suggestion"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/reports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["list_report_versions"];
        put?: never;
        /** @description Consolidar. De dos consolidaciones simultáneas solo una gana; la otra recibe 409 report.conflict. Lleva el cuerpo obligatorio { expected_cursor }, el cursor congelado al abrir el diálogo; si el resumen cambió, 409 report.view_outdated con el detail «El resumen cambió desde que abriste el diálogo. Revísalo de nuevo antes de consolidar.» (NFRD-U7-04). Un Markdown que pasa de report_max_bytes responde 413 limits.exceeded antes de escribir, con 0 filas y 0 archivos (NFR-U7-01). */
        post: operations["consolidate_report"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/correction-rounds": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["open_correction_round"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/correction-rounds/current/discard": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** @description Descarta la ronda de corrección abierta (estado discarded, con quién y cuándo; FD-U5-04). Sin copia abierta, 409 report.conflict. FD-U7-09 recoge X6 de U7. */
        post: operations["discard_correction_round"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/reports/{report_version_id}/download": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        /** @description Lectura de la vista previa: Content-Disposition inline; la consola no ofrece guardar el archivo. «Descargar reporte» llama a /exports (FD-U7-01). */
        get: operations["download_report"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/reports/{report_version_id}/exports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        /** @description Exportación con marca visible de usuario y hora, y el SHA-256 de la versión en la cabecera (US15.8). Solo el dueño y el admin; el investigador no (A-3). */
        post: operations["export_report"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/conductor-observations/{observation_id}/decision": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["decide_conductor_observation"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/conductor-observations/{observation_id}/audio": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["get_conductor_observation_audio"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/voice-turns": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["create_voice_turn"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/research-reports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["list_research_reports"];
        put?: never;
        /** @description Sube un reporte de la CLI (C19). Lo que no cumple el esquema se rechaza con 422 research.invalid_report sin guardar nada (P12). Si la petición no es multipart/form-data, 415 research.invalid_type; sin parte file, o con otra parte, 422 validation.invalid_request (NFR-U12-02). ConsoleApi pasa el catálogo de referencia de C18 en cada subida (FD-U12-06). */
        post: operations["upload_research_report"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/research-reports/{research_report_id}": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["get_research_report"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/research-reports/compare": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get: operations["compare_research_reports"];
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/sessions/{session_id}/retention": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post?: never;
        delete?: never;
        options?: never;
        head?: never;
        /** @description Cambia el plazo de retención de la sesión; lo valida EthicsGovernance contra C25 y lo escribe por EthicsSessionPort (FD-U13-05, FD-U13-08). */
        patch: operations["update_retention"];
        trace?: never;
    };
    "/acknowledgements": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["create_acknowledgement"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
    "/problem-reports": {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        get?: never;
        put?: never;
        post: operations["create_problem_report"];
        delete?: never;
        options?: never;
        head?: never;
        patch?: never;
        trace?: never;
    };
}
export type webhooks = Record<string, never>;
export interface components {
    schemas: {
        /**
         * Format: date-time
         * @description Formato único de fecha AAAA-MM-DDTHH:MM:SSZ en UTC (BR8.1, NFR11.2)
         */
        DateTime: string;
        Problem: {
            /** Format: uri-reference */
            type: string;
            title: string;
            status: number;
            code: components["schemas"]["ErrorCode"];
            /** @description Texto en español, sin datos sensibles */
            detail: string;
            instance?: string;
        };
        /** @enum {string} */
        ErrorCode: "auth.invalid_credentials" | "auth.unauthenticated" | "auth.forbidden" | "auth.csrf" | "auth.too_many_attempts" | "validation.invalid_request" | "limits.exceeded" | "route.not_found" | "system.internal" | "system.unavailable" | "user.duplicate_username" | "user.self_deactivation" | "user.last_admin" | "user.has_pending_sessions" | "user.not_found" | "user.weak_password" | "profile.not_approved" | "profile.transfer_not_authorized" | "session.not_owner" | "session.finalized" | "session.not_suspended" | "session.not_paused" | "session.not_finalized" | "session.suspended" | "session.consolidated" | "session.closed_to_new_turns" | "session.paused" | "session.terminated" | "session.blocked" | "session.consent_missing" | "session.consent_withdrawn" | "session.voice_not_authorized" | "import.invalid_type" | "import.invalid_transcript" | "import.profile_mismatch" | "retention.above_maximum" | "retention.below_minimum" | "retention.cannot_extend" | "ethics.text_version_outdated" | "problem_report.ids_mismatch" | "run.not_in_error" | "run.final_in_progress" | "analysis.invalid_output" | "analysis.content_blocked" | "analysis.timeout" | "analysis.provider" | "analysis.anonymizer_unavailable" | "anonymizer.profile_mismatch" | "anonymizer.destination_rejected" | "analysis.system" | "suggestion.not_found" | "review.observations_not_viewed" | "review.note_required" | "review.invalid_transition" | "review.round_locked" | "report.session_not_finalized" | "report.final_mode_not_launched" | "report.runs_in_progress" | "report.pending_suggestions" | "report.forbidden_vocabulary" | "report.conflict" | "report.view_outdated" | "report.integrity_mismatch" | "report.not_consolidated" | "report.not_found" | "report.export_not_recorded" | "research.invalid_report" | "research.invalid_type" | "research.not_found" | "research.duplicate" | "research.not_comparable" | "conductor_observation.not_approved" | "conductor_observation.not_found" | "conductor_observation.already_decided" | "conductor_observation.session_closed" | "speech.unavailable" | "speech.text_rejected";
        /** @enum {string} */
        Role: "analista" | "admin" | "investigador";
        Me: {
            /** Format: uuid */
            user_id: string;
            username: string;
            role: components["schemas"]["Role"];
            csrf_token: string;
            acknowledgement?: components["schemas"]["AcknowledgementStatus"];
        };
        User: {
            /** Format: uuid */
            user_id: string;
            username: string;
            role: components["schemas"]["Role"];
            active: boolean;
            created_at: components["schemas"]["DateTime"];
            /** @description Solo en GET /users y en la respuesta del PATCH; sesiones del usuario en cualquier estado distinto de consolidated, para la confirmación de M6 (FD-U3-04) */
            pending_sessions?: number;
        };
        /** @description Opaco: v1.<session_id>.<n> en base64url, donde n es el change_cursor de la sesión leído en la instantánea del sondeo. Uno mal formado, de otra sesión o mayor que el actual se trata como ausente (vista completa); la consola aplica cada respuesta como upsert por ID (NFRD-U4-05, NFRD-U7-04) */
        Cursor: string;
        /** @description Aviso de propósito limitado (VE-01), leído de C8 en ejecución; la consola no guarda copia */
        Notice: {
            text: string;
            version: string;
        };
        ProfileSummary: {
            profile_name: string;
            /** @enum {string} */
            purpose: "evaluation" | "demonstration" | "production";
            config_sha256: string;
            roles: {
                /** @enum {string} */
                role: "judge" | "verifier";
                commercial: boolean;
                /** @description true siempre que commercial es true (FR14.5) */
                via_anonymizer: boolean;
            }[];
            /** @description chunking.enabled del perfil (C18) */
            chunking_enabled?: boolean;
            /** @description Perfil de demostración que declara la misma familia (FR14.4) */
            same_family_warning?: boolean;
        };
        /** @description Bloque `consentimiento` de C6 (P11); sin datos personales. `registrado_en` lo completa el servidor con la hora del registro; si la petición lo trae, se ignora. */
        Consent: {
            /** @enum {string} */
            tipo: "persona" | "autoridad";
            version_texto: string;
            autoriza_transferencia: boolean;
            autoriza_voz: boolean;
            autoriza_conservar_audio: boolean;
            /** @description Solo un identificador de la constancia de la autoridad */
            constancia?: string;
            /** @description La persona es compareciente o tercero civil (VE-06) */
            requiere_mandato: boolean;
            /** @description Identificador de la constancia de mandato y garantías de la entidad; nunca un nombre */
            constancia_mandato?: string;
            readonly registrado_en?: components["schemas"]["DateTime"];
        } & (unknown & unknown);
        /**
         * @description Única representación de la pausa; PATCH /sessions/{id}/analysis pasa de open a paused y de vuelta (components, InterviewSession)
         * @enum {string}
         */
        SessionStatus: "open" | "paused" | "suspended" | "finalized" | "terminated" | "blocked" | "consolidated";
        Turn: {
            /** Format: uuid */
            turn_id: string;
            n: number;
            /** @enum {string} */
            hablante: "ENT" | "TEST";
            texto: string;
            /** @description Ausente en turnos guiados (P4 de iteracion2) */
            pagina?: number;
            pagina_fin?: number;
            /** @enum {string} */
            estado?: "visible" | "plegado";
            /** @enum {string} */
            origin: "typed" | "pasted" | "voice" | "imported";
            /**
             * @description Solo turnos de voz (SHOULD)
             * @enum {string}
             */
            voice_status?: "transcribing" | "transcribed" | "error";
            /** @description Solo turnos de voz en error: un code de C5 o session.consent_withdrawn (FD-U9-03) */
            voice_error_code?: components["schemas"]["ErrorCode"];
            submitted_at: components["schemas"]["DateTime"];
        };
        Run: {
            /** Format: uuid */
            run_id: string;
            /** @enum {string} */
            mode: "incremental" | "final";
            desde_turno: number;
            hasta_turno: number;
            /** @enum {string} */
            status: "queued" | "processing" | "done" | "error" | "cancelled";
            error_code?: components["schemas"]["ErrorCode"];
            attempt: number;
            profile_name: string;
            config_sha256: string;
            /** @description Copia tal cual de registro.fragmentado de C6 (regla 8). session-api lo llena al crear la corrida final con la configuración efectiva y al ingerir lo sustituye la copia de C6, con los mismos valores (NFRD-U6-18). Referencia canónica por $id (FD-U1-11) */
            fragmentado?: components["schemas"]["fragmentado"];
            /** @description true solo si todas las llamadas externas pasaron por el anonimizador; ausente si la corrida fue solo local (FD-U4-20, AC11.3.8) */
            anonymized?: boolean;
            requested_at: components["schemas"]["DateTime"];
            finished_at?: components["schemas"]["DateTime"];
        };
        /** @description Una fila de registro.llamadas de C6, copiada tal cual (regla 8); de solo lectura (FR15.3, AC12.5.3) */
        ModelCall: {
            /** @enum {string} */
            papel: "juez" | "verificador" | "verificador_permutado";
            proveedor: string;
            modelo: string;
            version?: string;
            esfuerzo_o_cuantizacion?: string;
            motor?: string;
            semilla?: number;
            tokens_entrada: number;
            tokens_salida: number;
            proveedor_alterno: boolean;
            anonimizado: boolean;
            fecha: components["schemas"]["DateTime"];
        };
        ReviewSuggestion: components["schemas"]["review-suggestion.v2"];
        ConductorObservation: {
            /** Format: uuid */
            observation_id: string;
            /** Format: uuid */
            run_id: string;
            /** @description Nunca contiene el texto de las citas (AC10.3.2) */
            tema: string;
            turnos: string[];
            /** @enum {string} */
            status: "proposed" | "approved" | "discarded";
            created_at: components["schemas"]["DateTime"];
        };
        SessionSummary: {
            /** Format: uuid */
            session_id: string;
            entrevista: string;
            /** Format: uuid */
            owner_user_id: string;
            owner_username?: string;
            status: components["schemas"]["SessionStatus"];
            /** @enum {string} */
            origin?: "guiada" | "corpus" | "sintetico";
            profile_name: string;
            created_at: components["schemas"]["DateTime"];
            finalized_at?: components["schemas"]["DateTime"];
            pending_suggestions: number;
        };
        SessionView: components["schemas"]["SessionSummary"] & {
            config_sha256: string;
            /** @description Opaco; se devuelve en el siguiente sondeo */
            cursor: components["schemas"]["Cursor"];
            closed_to_new_turns: boolean;
            /** @description FD-U13-04 */
            retention_days?: number;
            /** @description FD-U13-04 */
            retention_until?: components["schemas"]["DateTime"];
            /** @description FD-U13-04 */
            retention_default?: boolean;
            consent_withdrawn_at?: components["schemas"]["DateTime"];
            blocked_code?: components["schemas"]["ErrorCode"];
            turns: components["schemas"]["Turn"][];
            runs: components["schemas"]["Run"][];
            suggestions: components["schemas"]["review-suggestion.v2"][];
            conductor_observations?: components["schemas"]["ConductorObservation"][];
            can_consolidate: boolean;
            consolidation_blockers?: components["schemas"]["ErrorCode"][];
        };
        ReportVersion: {
            /** Format: uuid */
            report_version_id: string;
            /** Format: uuid */
            session_id: string;
            version_number: number;
            sha256: string;
            notice_version?: string;
            /** Format: uuid */
            consolidated_by: string;
            consolidated_at: components["schemas"]["DateTime"];
            /** Format: uuid */
            supersedes_version_id?: string;
        };
        /** @description Revisión 4 (FD-U12-05): suma schema_version, origin (local | zine, opcional), dataset_sha256 (opcional), measurement_valid, uploaded_by_username (lo resuelve ConsoleApi con IdentityAccess, porque el investigador no puede leer /users) y report_created_at. Entra con C19 v2 */
        ResearchReportSummary: {
            /** Format: uuid */
            research_report_id: string;
            schema_version?: string;
            /** @enum {string} */
            origin?: "local" | "zine";
            dataset_sha256?: string;
            measurement_valid?: boolean;
            uploaded_by_username?: string;
            report_created_at?: components["schemas"]["DateTime"];
            /** @enum {string} */
            kind: "run" | "evaluation";
            profile_name: string;
            config_sha256: string;
            prompt_sha256: string;
            analyzer_version: string;
            dataset_version?: string;
            /** @description SHA-256 del archivo subido; dos subidas iguales dan research.duplicate */
            source_sha256: string;
            /** Format: uuid */
            uploaded_by?: string;
            uploaded_at: components["schemas"]["DateTime"];
        };
        ResearchReportDetail: components["schemas"]["ResearchReportSummary"] & {
            run_summary?: Record<string, never>;
            price_table_version?: string;
            currency?: string;
            overall_passes?: boolean;
            blocking?: boolean;
            calls?: components["schemas"]["model-call.v1"][];
            totals?: components["schemas"]["totals"];
            metrics?: components["schemas"]["metrics"];
            bias_table?: components["schemas"]["bias_table"];
        };
        AcknowledgementStatus: {
            /**
             * @description Solo avisa; nunca impide abrir sesiones (VE-04, demostración)
             * @enum {string}
             */
            status: "valid" | "missing" | "expired" | "text_changed";
            text_version?: string;
            /** @description FD-U13-04 */
            current_text_version?: string;
            at?: components["schemas"]["DateTime"];
        };
        fragmentado: {
            activo: boolean;
            /** @description En turnos (C25) */
            ventana?: number;
            solapamiento?: number;
        };
        cita: {
            /** @description Texto literal; « […] » separa fragmentos del mismo turno en orden */
            cita: string;
            turno: string;
            /** @description Ausente si el turno no tiene página */
            pagina?: number;
            avisos?: ("turno_entrevistador" | "turno_plegado")[];
        };
        /**
         * Sugerencia de revisión (C7 v2)
         * @description El hallazgo de C6 convertido en sugerencia con estado editable; sin campos de veracidad (AUTONOMIA-03).
         */
        "review-suggestion.v2": {
            /** Format: uuid */
            suggestion_id: string;
            /** Format: uuid */
            session_id: string;
            /** Format: uuid */
            first_run_id: string;
            /** @description id del hallazgo en C6 de la corrida que lo propuso */
            hallazgo_id?: string;
            hecho: string;
            /** @enum {unknown} */
            tipo: "fecha" | "numero" | "lugar" | "persona" | "negacion" | "secuencia" | "otro";
            actos?: string[];
            cita_a: components["schemas"]["cita"];
            cita_b: components["schemas"]["cita"];
            observaciones: string;
            /** @enum {unknown} */
            state: "pending" | "accepted" | "edited" | "dismissed";
            note?: string;
            /** @description Del analista; nunca reemplaza hecho, tipo, citas ni observaciones */
            reformulation?: string;
            /** @description El usuario actual desplegó las observaciones (FR6.2) */
            observations_viewed: boolean;
            /** Format: uuid */
            decided_by?: string;
            /** Format: date-time */
            decided_at?: string;
        } & (unknown & unknown & unknown);
        /** @description Sin espacios; nombres de modelo, versiones, esfuerzos y motores */
        token: string;
        count: number;
        /**
         * Registro de una llamada a un modelo (C13)
         * @description Misma forma que `ModelCall` de `veridicus_contracts.model_calls`. El papel es una cadena con patrón y no una lista cerrada (BR9.1, FD-U1-01): el analizador lo restringe a `judge`, `verifier` y `verifier_permuted` en C18 y en C19. Estricto y sin texto libre: toda cadena tiene patrón sin espacios o formato cerrado y todo entero, tope (NFR1.4).
         */
        "model-call.v1": {
            role: string;
            /** @enum {unknown} */
            provider: "anthropic" | "google" | "openai" | "local";
            model: components["schemas"]["token"];
            version?: components["schemas"]["token"];
            effort_or_quantization?: components["schemas"]["token"];
            engine?: components["schemas"]["token"];
            seed?: number;
            input_tokens: components["schemas"]["count"];
            output_tokens: components["schemas"]["count"];
            /** @description true cuando la llamada fue al proveedor alterno del perfil (FR15.2) */
            fallback_provider: boolean;
            /** @description false con un destino local; false con un destino externo es un incidente */
            anonymized: boolean;
            /** Format: date-time */
            at: string;
            $defs: {
                /** @description Sin espacios; nombres de modelo, versiones, esfuerzos y motores */
                token: string;
                count: number;
            };
        };
        "$defs-token": string;
        totals: {
            input_tokens: components["schemas"]["count"];
            output_tokens: components["schemas"]["count"];
            estimated_cost?: number;
            price_table_version?: components["schemas"]["$defs-token"];
        };
        ratio: number;
        /** @description Métrica con valor en [0, 1] (BR12.3, MetricResult) */
        metric_ratio: {
            per_run: components["schemas"]["ratio"][];
            aggregate: components["schemas"]["ratio"];
            threshold?: components["schemas"]["ratio"];
            passes?: boolean;
        };
        /** @description Fracción sin valor por corrida: three_run_agreement, scenario_a_difference (entities.md MetricResult, BR12.6) */
        metric_ratio_without_runs: {
            aggregate: components["schemas"]["ratio"];
            threshold?: components["schemas"]["ratio"];
            passes?: boolean;
        };
        /** @description Métrica entera acotada con valor por corrida (anonymizer_leaks) */
        metric_count: {
            per_run: components["schemas"]["count"][];
            aggregate: components["schemas"]["count"];
            threshold?: components["schemas"]["count"];
            passes?: boolean;
        };
        /** @description Entero sin valor por corrida (scenario_a_marker_hits, BR12.6) */
        metric_count_without_runs: {
            aggregate: components["schemas"]["count"];
            threshold?: components["schemas"]["count"];
            passes?: boolean;
        };
        /** @description Solo con kind evaluation (NFR4, NFR5, BR12.3); los umbrales los fija evaluation/thresholds.v1.yaml */
        metrics: {
            verified_quotes?: components["schemas"]["metric_ratio"];
            json_format_errors?: components["schemas"]["metric_ratio"];
            permutation_coverage?: components["schemas"]["metric_ratio"];
            completed_runs?: components["schemas"]["metric_ratio"];
            precision?: components["schemas"]["metric_ratio"];
            recall?: components["schemas"]["metric_ratio"];
            reversed_order_consistency?: components["schemas"]["metric_ratio"];
            three_run_agreement?: components["schemas"]["metric_ratio_without_runs"];
            type_agreement?: components["schemas"]["metric_ratio"];
            scenario_a_difference?: components["schemas"]["metric_ratio_without_runs"];
            anonymizer_leaks?: components["schemas"]["metric_count"];
            scenario_a_marker_hits?: components["schemas"]["metric_count_without_runs"];
        };
        /** @description <tipo_hecho>__<perfil_persona> (FD-U11-07) */
        synthetic_set: string;
        /** @description VE-17; por tipo de hecho y por conjunto sintético */
        bias_table: {
            /** @enum {unknown} */
            fact_type: "fecha" | "numero" | "lugar" | "persona" | "negacion" | "secuencia" | "otro";
            synthetic_set: components["schemas"]["synthetic_set"];
            expected: components["schemas"]["count"];
            found: components["schemas"]["count"];
        }[];
    };
    responses: {
        /** @description Error en formato Problem Details (RFC 9457) */
        Problem: {
            headers: {
                [name: string]: unknown;
            };
            content: {
                "application/problem+json": components["schemas"]["Problem"];
            };
        };
    };
    parameters: {
        CsrfToken: string;
        SessionId: string;
        Since: components["schemas"]["Cursor"];
        RunId: string;
        SuggestionId: string;
    };
    requestBodies: never;
    headers: never;
    pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
    login: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    username: string;
                    password: string;
                };
            };
        };
        responses: {
            /** @description Sesión creada; responde Set-Cookie veridicus_session (HttpOnly, Secure, SameSite=Strict) */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            401: components["responses"]["Problem"];
            413: components["responses"]["Problem"];
            /** @description auth.too_many_attempts, con Retry-After (FD-U3-02) */
            429: {
                headers: {
                    "Retry-After"?: number;
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["Problem"];
                };
            };
            /** @description Cola del semáforo llena; documenta Retry-After (FD-U3-02, NFRD-U3-10) */
            503: {
                headers: {
                    "Retry-After"?: number;
                    [name: string]: unknown;
                };
                content: {
                    "application/problem+json": components["schemas"]["Problem"];
                };
            };
        };
    };
    logout: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Sesión revocada */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            401: components["responses"]["Problem"];
        };
    };
    get_me: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Usuario actual, token anti-CSRF y estado del reconocimiento */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Me"];
                };
            };
            401: components["responses"]["Problem"];
        };
    };
    list_users: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Usuarios */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["User"][];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
        };
    };
    create_user: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    username: string;
                    password: string;
                    role: components["schemas"]["Role"];
                };
            };
        };
        responses: {
            /** @description Usuario creado */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["User"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description user.duplicate_username (FD-U3-02) */
            409: components["responses"]["Problem"];
            413: components["responses"]["Problem"];
            /** @description user.weak_password o validation.invalid_request (FD-U3-02) */
            422: components["responses"]["Problem"];
        };
    };
    update_user: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                user_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    active?: boolean;
                    role?: components["schemas"]["Role"];
                };
            };
        };
        responses: {
            /** @description Usuario actualizado; deja fila en el historial de usuario */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["User"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description user.not_found (FD-U3-02) */
            404: components["responses"]["Problem"];
            /** @description user.has_pending_sessions (cambio de rol con sesiones pendientes), user.self_deactivation o user.last_admin (FD-U3-02, E-12) */
            409: components["responses"]["Problem"];
            /** @description user.weak_password o validation.invalid_request (FD-U3-02) */
            422: components["responses"]["Problem"];
        };
    };
    get_notice: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Texto y versión del aviso de VE-01 */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Notice"];
                };
            };
        };
    };
    list_profiles: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Solo los perfiles aprobados (C18), con su indicación de proveedor comercial (FR14.5) */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ProfileSummary"][];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
        };
    };
    list_sessions: {
        parameters: {
            query?: {
                status?: components["schemas"]["SessionStatus"];
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Lista de sesiones */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionSummary"][];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
        };
    };
    create_session: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    entrevista: string;
                    profile_name: string;
                    consentimiento: components["schemas"]["Consent"];
                    /** @description Opcional; lo valida EthicsGovernance contra C25 (FD-U13-04) */
                    retention_days?: number;
                };
            };
        };
        responses: {
            /** @description Sesión abierta y ligada al perfil y a su config_sha256 (FR3.1) */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionView"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            413: components["responses"]["Problem"];
            422: components["responses"]["Problem"];
        };
    };
    import_session: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": {
                    /**
                     * Format: binary
                     * @description JSON de la entrada de C6 (FD-U6-03)
                     */
                    file: string;
                    profile_name: string;
                    /** @description Opcional (FD-U13-04) */
                    retention_days?: number;
                };
            };
        };
        responses: {
            /** @description Sesión importada */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionView"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            413: components["responses"]["Problem"];
            /** @description import.invalid_type (FD-U6-03) */
            415: components["responses"]["Problem"];
            422: components["responses"]["Problem"];
        };
    };
    get_session: {
        parameters: {
            query?: {
                since?: components["parameters"]["Since"];
            };
            header?: never;
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Vista de la sesión */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionView"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
        };
    };
    heartbeat_session: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Latido sin corridas en proceso */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
        };
    };
    create_turn: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    /** @enum {string} */
                    hablante: "ENT" | "TEST";
                    texto: string;
                    /**
                     * Format: uuid
                     * @description Evita turnos duplicados si el navegador reenvía
                     */
                    client_request_id: string;
                };
            };
        };
        responses: {
            /** @description Turno numerado; la corrida queda en cola y no se espera */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        turn: components["schemas"]["Turn"];
                        run?: components["schemas"]["Run"];
                    };
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            409: components["responses"]["Problem"];
            413: components["responses"]["Problem"];
        };
    };
    paste_transcript: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    text: string;
                    /** Format: uuid */
                    client_request_id: string;
                };
            };
        };
        responses: {
            /** @description Turnos numerados en orden y una corrida en cola */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        turns: components["schemas"]["Turn"][];
                        run?: components["schemas"]["Run"];
                    };
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            409: components["responses"]["Problem"];
            413: components["responses"]["Problem"];
        };
    };
    launch_final_run: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Corrida final en cola */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Run"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description Code de la situación (FD-U6-17): run.final_in_progress, session.not_finalized (guiada sin finalizar, FD-U6-02), session.paused, session.suspended, session.consolidated, session.blocked, session.terminated o session.consent_withdrawn */
            409: components["responses"]["Problem"];
        };
    };
    retry_run: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
                run_id: components["parameters"]["RunId"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Misma corrida, mismo tramo, attempt + 1 */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Run"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description La corrida no está en error (run.not_in_error) o la sesión no admite corridas (session.blocked, session.consent_withdrawn, session.terminated, session.paused, session.consolidated; FD-U4-05) */
            409: components["responses"]["Problem"];
        };
    };
    list_model_calls: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: components["parameters"]["SessionId"];
                run_id: components["parameters"]["RunId"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Registro de modelos de la corrida, solo lectura (US12.5) */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ModelCall"][];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
        };
    };
    set_analysis_paused: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    paused: boolean;
                };
            };
        };
        responses: {
            /** @description Sesión actualizada; al reanudar, la corrida queda en cola (C-3) */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionView"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description Code de la situación (FD-U6-17): session.not_paused al reanudar sin pausa (FD-U6-01), session.suspended, session.consolidated y los demás estados que no admiten el cambio */
            409: components["responses"]["Problem"];
        };
    };
    terminate_session: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Sesión terminada */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionView"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description Code de la situación de la tabla §3 del Functional Design de U6 (FD-U6-17) */
            409: components["responses"]["Problem"];
        };
    };
    withdraw_consent: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Retirada registrada */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionView"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description Code de la situación de la tabla §3 del Functional Design de U6 (FD-U6-17) */
            409: components["responses"]["Problem"];
        };
    };
    resume_session: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Sesión suspendida vuelve a abierta desde el último turno registrado */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionView"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            409: components["responses"]["Problem"];
        };
    };
    finalize_session: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Sesión finalizada (también desde suspendida); empieza la medición de MTTV */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionView"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            409: components["responses"]["Problem"];
            422: components["responses"]["Problem"];
            503: components["responses"]["Problem"];
        };
    };
    view_observations: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                suggestion_id: components["parameters"]["SuggestionId"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description «Observaciones desplegadas» registradas (solo inserción) y acceso registrado (C23) */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description suggestion.not_found (FD-U5-01, NFR-U5-05) */
            404: components["responses"]["Problem"];
        };
    };
    decide_suggestion: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                suggestion_id: components["parameters"]["SuggestionId"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    /** @enum {string} */
                    state: "accepted" | "edited" | "dismissed";
                    /** @description Obligatoria y no vacía si state es dismissed */
                    note?: string;
                    /** @description Obligatoria si state es edited; nunca cambia hecho, tipo, citas ni observaciones */
                    reformulation?: string;
                };
            };
        };
        responses: {
            /** @description Decisión registrada en la ronda abierta */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["review-suggestion.v2"];
                };
            };
            401: components["responses"]["Problem"];
            /** @description auth.forbidden, session.not_owner o auth.csrf (NFR-U5-05) */
            403: components["responses"]["Problem"];
            /** @description suggestion.not_found (FD-U5-01, NFR-U5-05) */
            404: components["responses"]["Problem"];
            /** @description Ronda bloqueada, observaciones no desplegadas, nota faltante o transición inválida */
            409: components["responses"]["Problem"];
            /** @description limits.exceeded (FD-U5-02, NFR-U1-03, NFR-U5-05) */
            413: components["responses"]["Problem"];
            /** @description review.note_required o validation.invalid_request (NFR-U5-05) */
            422: components["responses"]["Problem"];
        };
    };
    list_report_versions: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Versiones del reporte */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReportVersion"][];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
        };
    };
    consolidate_report: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    expected_cursor: components["schemas"]["Cursor"];
                };
            };
        };
        responses: {
            /** @description Reporte consolidado, guardado y con su SHA-256 */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ReportVersion"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            409: components["responses"]["Problem"];
            413: components["responses"]["Problem"];
            422: components["responses"]["Problem"];
            503: components["responses"]["Problem"];
        };
    };
    open_correction_round: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Abre o retoma la única ronda de corrección, que parte de la versión vigente */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            409: components["responses"]["Problem"];
            422: components["responses"]["Problem"];
            503: components["responses"]["Problem"];
        };
    };
    discard_correction_round: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Ronda de corrección descartada */
            204: {
                headers: {
                    [name: string]: unknown;
                };
                content?: never;
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            409: components["responses"]["Problem"];
            422: components["responses"]["Problem"];
            503: components["responses"]["Problem"];
        };
    };
    download_report: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                report_version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Markdown del reporte (text/markdown; charset=utf-8); el servidor recalcula el SHA-256 antes de enviarlo (NFR10.4) */
            200: {
                headers: {
                    "X-Veridicus-SHA256"?: string;
                    "Content-Disposition"?: "inline";
                    "X-Content-Type-Options"?: "nosniff";
                    "Cache-Control"?: "no-store";
                    [name: string]: unknown;
                };
                content: {
                    "text/markdown": string;
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description El archivo no coincide con el SHA-256 registrado (report.integrity_mismatch) o no hay versión (report.not_consolidated) */
            409: components["responses"]["Problem"];
            422: components["responses"]["Problem"];
            503: components["responses"]["Problem"];
        };
    };
    export_report: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                report_version_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Archivo exportado (text/markdown; charset=utf-8); cada exportación es un artefacto propio con su hash, registrado por C23 (NFR10.4) */
            201: {
                headers: {
                    "X-Veridicus-Export-SHA256"?: string;
                    "Content-Disposition"?: string;
                    "X-Content-Type-Options"?: "nosniff";
                    "Cache-Control"?: "no-store";
                    [name: string]: unknown;
                };
                content: {
                    "text/markdown": string;
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description report.not_found (FD-U7-05) */
            404: components["responses"]["Problem"];
            409: components["responses"]["Problem"];
            422: components["responses"]["Problem"];
            /** @description report.export_not_recorded: AccessLog falló o venció en 500 ms y se revirtió la transacción (FD-U7-05, NFR-U7-09) */
            503: components["responses"]["Problem"];
        };
    };
    decide_conductor_observation: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                observation_id: string;
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    /** @enum {string} */
                    status: "approved" | "discarded";
                };
            };
        };
        responses: {
            /** @description Decisión del analista sobre la aclaración */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ConductorObservation"];
                };
            };
            401: components["responses"]["Problem"];
            /** @description session.not_owner, auth.forbidden o auth.csrf (FD-U8-02) */
            403: components["responses"]["Problem"];
            /** @description conductor_observation.not_found (FD-U8-02) */
            404: components["responses"]["Problem"];
            /** @description conductor_observation.already_decided o conductor_observation.session_closed (FD-U8-02) */
            409: components["responses"]["Problem"];
            /** @description limits.exceeded (NFRD-U8-05) */
            413: components["responses"]["Problem"];
        };
    };
    get_conductor_observation_audio: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                observation_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Audio sintetizado en el clúster solo para una aclaración aprobada que cumple DT23 */
            200: {
                headers: {
                    "Cache-Control"?: "no-store";
                    [name: string]: unknown;
                };
                content: {
                    "audio/wav": string;
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description conductor_observation.not_found (FD-U9-02) */
            404: components["responses"]["Problem"];
            /** @description La aclaración no está aprobada (conductor_observation.not_approved), el texto se rechazó (speech.text_rejected) o el estado de la sesión no lo admite (BR5.7 de U9) (FD-U9-02) */
            409: components["responses"]["Problem"];
            /** @description speech.unavailable (FD-U9-02) */
            503: components["responses"]["Problem"];
        };
    };
    create_voice_turn: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": {
                    /**
                     * Format: binary
                     * @description WAV mono de 16 kHz o MP3
                     */
                    audio: string;
                    /** @enum {string} */
                    hablante: "ENT" | "TEST";
                    /** Format: uuid */
                    client_request_id: string;
                };
            };
        };
        responses: {
            /** @description Turno de voz numerado en transcribing */
            202: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["Turn"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description Sin autorización de voz (session.voice_not_authorized) */
            409: components["responses"]["Problem"];
            /** @description limits.exceeded por voice_body_max_bytes o audio_max_bytes (NFRD-U9-03) */
            413: components["responses"]["Problem"];
            415: components["responses"]["Problem"];
        };
    };
    list_research_reports: {
        parameters: {
            query?: never;
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Reportes subidos */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResearchReportSummary"][];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
        };
    };
    upload_research_report: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "multipart/form-data": {
                    /**
                     * Format: binary
                     * @description JSON de C19
                     */
                    file: string;
                };
            };
        };
        responses: {
            /** @description Reporte guardado (solo cifras) */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResearchReportDetail"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description El mismo archivo ya se subió (research.duplicate) */
            409: components["responses"]["Problem"];
            413: components["responses"]["Problem"];
            /** @description research.invalid_type (NFR-U12-02) */
            415: components["responses"]["Problem"];
            422: components["responses"]["Problem"];
        };
    };
    get_research_report: {
        parameters: {
            query?: never;
            header?: never;
            path: {
                research_report_id: string;
            };
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Detalle */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["ResearchReportDetail"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description research.not_found (FD-U12-04) */
            404: components["responses"]["Problem"];
        };
    };
    compare_research_reports: {
        parameters: {
            query: {
                a: string;
                b: string;
            };
            header?: never;
            path?: never;
            cookie?: never;
        };
        requestBody?: never;
        responses: {
            /** @description Las cifras de los dos reportes lado a lado */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": [
                        components["schemas"]["ResearchReportDetail"],
                        components["schemas"]["ResearchReportDetail"]
                    ];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            /** @description research.not_found (FD-U12-04) */
            404: components["responses"]["Problem"];
            /** @description Reportes de tipo distinto (research.not_comparable) */
            409: components["responses"]["Problem"];
            /** @description validation.invalid_request cuando a = b (FD-U12-04) */
            422: components["responses"]["Problem"];
        };
    };
    update_retention: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path: {
                session_id: components["parameters"]["SessionId"];
            };
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    retention_days: number;
                };
            };
        };
        responses: {
            /** @description Plazo actualizado */
            200: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["SessionView"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            413: components["responses"]["Problem"];
            /** @description retention.above_maximum, retention.below_minimum o retention.cannot_extend (FD-U13-04) */
            422: components["responses"]["Problem"];
        };
    };
    create_acknowledgement: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    text_version: string;
                };
            };
        };
        responses: {
            /** @description Reconocimiento registrado (VE-04) */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": components["schemas"]["AcknowledgementStatus"];
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            413: components["responses"]["Problem"];
            /** @description ethics.text_version_outdated (FD-U13-04, E-12) */
            422: components["responses"]["Problem"];
        };
    };
    create_problem_report: {
        parameters: {
            query?: never;
            header: {
                "X-CSRF-Token": components["parameters"]["CsrfToken"];
            };
            path?: never;
            cookie?: never;
        };
        requestBody: {
            content: {
                "application/json": {
                    /** @enum {string} */
                    category: "harmful_finding" | "improper_vocabulary" | "mismatched_quote" | "interviewee_distress" | "anonymization_failure" | "misuse";
                    /** Format: uuid */
                    session_id?: string;
                    /**
                     * Format: uuid
                     * @description Si viene, session_id se deriva de la sugerencia; si los dos vienen y no coinciden, 422 problem_report.ids_mismatch (FD-U13-04, FD-U13-07)
                     */
                    suggestion_id?: string;
                    /** @description Opcional (FD-U13-06) */
                    note?: string;
                };
            };
        };
        responses: {
            /** @description Reporte guardado; avisa, sin rechazar, si la nota trae testimony_warning_words (C25) o más palabras seguidas de un turno (VE-15) */
            201: {
                headers: {
                    [name: string]: unknown;
                };
                content: {
                    "application/json": {
                        /** Format: uuid */
                        problem_report_id: string;
                        testimony_warning: boolean;
                    };
                };
            };
            401: components["responses"]["Problem"];
            403: components["responses"]["Problem"];
            404: components["responses"]["Problem"];
            413: components["responses"]["Problem"];
            422: components["responses"]["Problem"];
        };
    };
}
