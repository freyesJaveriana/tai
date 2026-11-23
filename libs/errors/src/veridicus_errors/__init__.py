"""Excepciones de Veridicus: una clase sin lógica por `code` del catálogo (BR7.4).

El estado HTTP no vive aquí sino en `contracts/errors/error-codes.v2.yaml`; el manejador que
traduce a Problem Details es de cada servicio. Las bases de familia no llevan `code`.
"""

from typing import ClassVar


class VeridicusError(Exception):
    """Raíz de la jerarquía única de excepciones."""


class AuthFamilyError(VeridicusError):
    """Familia `auth.*`."""


class ValidationFamilyError(VeridicusError):
    """Familia `validation.*`."""


class LimitsFamilyError(VeridicusError):
    """Familia `limits.*`."""


class RouteFamilyError(VeridicusError):
    """Familia `route.*`."""


class SystemFamilyError(VeridicusError):
    """Familia `system.*`."""


class UserFamilyError(VeridicusError):
    """Familia `user.*`."""


class ProfileFamilyError(VeridicusError):
    """Familia `profile.*`."""


class SessionFamilyError(VeridicusError):
    """Familia `session.*`."""


class ImportFamilyError(VeridicusError):
    """Familia `import.*`."""


class RetentionFamilyError(VeridicusError):
    """Familia `retention.*`."""


class EthicsFamilyError(VeridicusError):
    """Familia `ethics.*`."""


class ProblemReportFamilyError(VeridicusError):
    """Familia `problem_report.*`."""


class RunFamilyError(VeridicusError):
    """Familia `run.*`."""


class AnalysisFamilyError(VeridicusError):
    """Familia `analysis.*`."""


class AnonymizerFamilyError(VeridicusError):
    """Familia `anonymizer.*`."""


class SuggestionFamilyError(VeridicusError):
    """Familia `suggestion.*`."""


class ReviewFamilyError(VeridicusError):
    """Familia `review.*`."""


class ReportFamilyError(VeridicusError):
    """Familia `report.*`."""


class ResearchFamilyError(VeridicusError):
    """Familia `research.*`."""


class ConductorObservationFamilyError(VeridicusError):
    """Familia `conductor_observation.*`."""


class SpeechFamilyError(VeridicusError):
    """Familia `speech.*`."""


class ConfigFamilyError(VeridicusError):
    """Familia `config.*`."""


class AuthInvalidCredentialsError(AuthFamilyError):
    """`auth.invalid_credentials`."""

    code: ClassVar[str] = "auth.invalid_credentials"


class AuthUnauthenticatedError(AuthFamilyError):
    """`auth.unauthenticated`."""

    code: ClassVar[str] = "auth.unauthenticated"


class AuthForbiddenError(AuthFamilyError):
    """`auth.forbidden`."""

    code: ClassVar[str] = "auth.forbidden"


class AuthCsrfError(AuthFamilyError):
    """`auth.csrf`."""

    code: ClassVar[str] = "auth.csrf"


class AuthTooManyAttemptsError(AuthFamilyError):
    """`auth.too_many_attempts`."""

    code: ClassVar[str] = "auth.too_many_attempts"


class ValidationInvalidRequestError(ValidationFamilyError):
    """`validation.invalid_request`."""

    code: ClassVar[str] = "validation.invalid_request"


class LimitsExceededError(LimitsFamilyError):
    """`limits.exceeded`."""

    code: ClassVar[str] = "limits.exceeded"


class RouteNotFoundError(RouteFamilyError):
    """`route.not_found`."""

    code: ClassVar[str] = "route.not_found"


class SystemInternalError(SystemFamilyError):
    """`system.internal`."""

    code: ClassVar[str] = "system.internal"


class SystemUnavailableError(SystemFamilyError):
    """`system.unavailable`."""

    code: ClassVar[str] = "system.unavailable"


class UserDuplicateUsernameError(UserFamilyError):
    """`user.duplicate_username`."""

    code: ClassVar[str] = "user.duplicate_username"


class UserSelfDeactivationError(UserFamilyError):
    """`user.self_deactivation`."""

    code: ClassVar[str] = "user.self_deactivation"


class UserLastAdminError(UserFamilyError):
    """`user.last_admin`."""

    code: ClassVar[str] = "user.last_admin"


class UserHasPendingSessionsError(UserFamilyError):
    """`user.has_pending_sessions`."""

    code: ClassVar[str] = "user.has_pending_sessions"


class UserNotFoundError(UserFamilyError):
    """`user.not_found`."""

    code: ClassVar[str] = "user.not_found"


class UserWeakPasswordError(UserFamilyError):
    """`user.weak_password`."""

    code: ClassVar[str] = "user.weak_password"


class ProfileNotApprovedError(ProfileFamilyError):
    """`profile.not_approved`."""

    code: ClassVar[str] = "profile.not_approved"


class ProfileTransferNotAuthorizedError(ProfileFamilyError):
    """`profile.transfer_not_authorized`."""

    code: ClassVar[str] = "profile.transfer_not_authorized"


class SessionNotOwnerError(SessionFamilyError):
    """`session.not_owner`."""

    code: ClassVar[str] = "session.not_owner"


class SessionFinalizedError(SessionFamilyError):
    """`session.finalized`."""

    code: ClassVar[str] = "session.finalized"


class SessionNotSuspendedError(SessionFamilyError):
    """`session.not_suspended`."""

    code: ClassVar[str] = "session.not_suspended"


class SessionNotPausedError(SessionFamilyError):
    """`session.not_paused`."""

    code: ClassVar[str] = "session.not_paused"


class SessionNotFinalizedError(SessionFamilyError):
    """`session.not_finalized`."""

    code: ClassVar[str] = "session.not_finalized"


class SessionSuspendedError(SessionFamilyError):
    """`session.suspended`."""

    code: ClassVar[str] = "session.suspended"


class SessionConsolidatedError(SessionFamilyError):
    """`session.consolidated`."""

    code: ClassVar[str] = "session.consolidated"


class SessionClosedToNewTurnsError(SessionFamilyError):
    """`session.closed_to_new_turns`."""

    code: ClassVar[str] = "session.closed_to_new_turns"


class SessionPausedError(SessionFamilyError):
    """`session.paused`."""

    code: ClassVar[str] = "session.paused"


class SessionTerminatedError(SessionFamilyError):
    """`session.terminated`."""

    code: ClassVar[str] = "session.terminated"


class SessionBlockedError(SessionFamilyError):
    """`session.blocked`."""

    code: ClassVar[str] = "session.blocked"


class SessionConsentMissingError(SessionFamilyError):
    """`session.consent_missing`."""

    code: ClassVar[str] = "session.consent_missing"


class SessionConsentWithdrawnError(SessionFamilyError):
    """`session.consent_withdrawn`."""

    code: ClassVar[str] = "session.consent_withdrawn"


class SessionVoiceNotAuthorizedError(SessionFamilyError):
    """`session.voice_not_authorized`."""

    code: ClassVar[str] = "session.voice_not_authorized"


class ImportInvalidTypeError(ImportFamilyError):
    """`import.invalid_type`."""

    code: ClassVar[str] = "import.invalid_type"


class ImportInvalidTranscriptError(ImportFamilyError):
    """`import.invalid_transcript`."""

    code: ClassVar[str] = "import.invalid_transcript"


class ImportProfileMismatchError(ImportFamilyError):
    """`import.profile_mismatch`."""

    code: ClassVar[str] = "import.profile_mismatch"


class RetentionAboveMaximumError(RetentionFamilyError):
    """`retention.above_maximum`."""

    code: ClassVar[str] = "retention.above_maximum"


class RetentionBelowMinimumError(RetentionFamilyError):
    """`retention.below_minimum`."""

    code: ClassVar[str] = "retention.below_minimum"


class RetentionCannotExtendError(RetentionFamilyError):
    """`retention.cannot_extend`."""

    code: ClassVar[str] = "retention.cannot_extend"


class EthicsTextVersionOutdatedError(EthicsFamilyError):
    """`ethics.text_version_outdated`."""

    code: ClassVar[str] = "ethics.text_version_outdated"


class ProblemReportIdsMismatchError(ProblemReportFamilyError):
    """`problem_report.ids_mismatch`."""

    code: ClassVar[str] = "problem_report.ids_mismatch"


class RunNotInErrorError(RunFamilyError):
    """`run.not_in_error`."""

    code: ClassVar[str] = "run.not_in_error"


class RunFinalInProgressError(RunFamilyError):
    """`run.final_in_progress`."""

    code: ClassVar[str] = "run.final_in_progress"


class AnalysisInvalidOutputError(AnalysisFamilyError):
    """`analysis.invalid_output`."""

    code: ClassVar[str] = "analysis.invalid_output"


class AnalysisContentBlockedError(AnalysisFamilyError):
    """`analysis.content_blocked`."""

    code: ClassVar[str] = "analysis.content_blocked"


class AnalysisTimeoutError(AnalysisFamilyError):
    """`analysis.timeout`."""

    code: ClassVar[str] = "analysis.timeout"


class AnalysisProviderError(AnalysisFamilyError):
    """`analysis.provider`."""

    code: ClassVar[str] = "analysis.provider"


class AnalysisAnonymizerUnavailableError(AnalysisFamilyError):
    """`analysis.anonymizer_unavailable`."""

    code: ClassVar[str] = "analysis.anonymizer_unavailable"


class AnonymizerIncidentError(AnonymizerFamilyError):
    """`anonymizer.incident`."""

    code: ClassVar[str] = "anonymizer.incident"


class AnonymizerProfileMismatchError(AnonymizerFamilyError):
    """`anonymizer.profile_mismatch`."""

    code: ClassVar[str] = "anonymizer.profile_mismatch"


class AnonymizerDestinationRejectedError(AnonymizerFamilyError):
    """`anonymizer.destination_rejected`."""

    code: ClassVar[str] = "anonymizer.destination_rejected"


class AnalysisSystemError(AnalysisFamilyError):
    """`analysis.system`."""

    code: ClassVar[str] = "analysis.system"


class SuggestionNotFoundError(SuggestionFamilyError):
    """`suggestion.not_found`."""

    code: ClassVar[str] = "suggestion.not_found"


class ReviewObservationsNotViewedError(ReviewFamilyError):
    """`review.observations_not_viewed`."""

    code: ClassVar[str] = "review.observations_not_viewed"


class ReviewNoteRequiredError(ReviewFamilyError):
    """`review.note_required`."""

    code: ClassVar[str] = "review.note_required"


class ReviewInvalidTransitionError(ReviewFamilyError):
    """`review.invalid_transition`."""

    code: ClassVar[str] = "review.invalid_transition"


class ReviewRoundLockedError(ReviewFamilyError):
    """`review.round_locked`."""

    code: ClassVar[str] = "review.round_locked"


class ReportSessionNotFinalizedError(ReportFamilyError):
    """`report.session_not_finalized`."""

    code: ClassVar[str] = "report.session_not_finalized"


class ReportFinalModeNotLaunchedError(ReportFamilyError):
    """`report.final_mode_not_launched`."""

    code: ClassVar[str] = "report.final_mode_not_launched"


class ReportRunsInProgressError(ReportFamilyError):
    """`report.runs_in_progress`."""

    code: ClassVar[str] = "report.runs_in_progress"


class ReportPendingSuggestionsError(ReportFamilyError):
    """`report.pending_suggestions`."""

    code: ClassVar[str] = "report.pending_suggestions"


class ReportForbiddenVocabularyError(ReportFamilyError):
    """`report.forbidden_vocabulary`."""

    code: ClassVar[str] = "report.forbidden_vocabulary"


class ReportConflictError(ReportFamilyError):
    """`report.conflict`."""

    code: ClassVar[str] = "report.conflict"


class ReportViewOutdatedError(ReportFamilyError):
    """`report.view_outdated`."""

    code: ClassVar[str] = "report.view_outdated"


class ReportIntegrityMismatchError(ReportFamilyError):
    """`report.integrity_mismatch`."""

    code: ClassVar[str] = "report.integrity_mismatch"


class ReportNotConsolidatedError(ReportFamilyError):
    """`report.not_consolidated`."""

    code: ClassVar[str] = "report.not_consolidated"


class ReportNotFoundError(ReportFamilyError):
    """`report.not_found`."""

    code: ClassVar[str] = "report.not_found"


class ReportExportNotRecordedError(ReportFamilyError):
    """`report.export_not_recorded`."""

    code: ClassVar[str] = "report.export_not_recorded"


class ResearchInvalidReportError(ResearchFamilyError):
    """`research.invalid_report`."""

    code: ClassVar[str] = "research.invalid_report"


class ResearchInvalidTypeError(ResearchFamilyError):
    """`research.invalid_type`."""

    code: ClassVar[str] = "research.invalid_type"


class ResearchNotFoundError(ResearchFamilyError):
    """`research.not_found`."""

    code: ClassVar[str] = "research.not_found"


class ResearchDuplicateError(ResearchFamilyError):
    """`research.duplicate`."""

    code: ClassVar[str] = "research.duplicate"


class ResearchNotComparableError(ResearchFamilyError):
    """`research.not_comparable`."""

    code: ClassVar[str] = "research.not_comparable"


class ConductorObservationNotApprovedError(ConductorObservationFamilyError):
    """`conductor_observation.not_approved`."""

    code: ClassVar[str] = "conductor_observation.not_approved"


class ConductorObservationNotFoundError(ConductorObservationFamilyError):
    """`conductor_observation.not_found`."""

    code: ClassVar[str] = "conductor_observation.not_found"


class ConductorObservationAlreadyDecidedError(ConductorObservationFamilyError):
    """`conductor_observation.already_decided`."""

    code: ClassVar[str] = "conductor_observation.already_decided"


class ConductorObservationSessionClosedError(ConductorObservationFamilyError):
    """`conductor_observation.session_closed`."""

    code: ClassVar[str] = "conductor_observation.session_closed"


class SpeechUnavailableError(SpeechFamilyError):
    """`speech.unavailable`."""

    code: ClassVar[str] = "speech.unavailable"


class SpeechTextRejectedError(SpeechFamilyError):
    """`speech.text_rejected`."""

    code: ClassVar[str] = "speech.text_rejected"


class ConfigInvalidProfileError(ConfigFamilyError):
    """`config.invalid_profile`."""

    code: ClassVar[str] = "config.invalid_profile"


class ConfigInvalidLimitError(ConfigFamilyError):
    """`config.invalid_limit`."""

    code: ClassVar[str] = "config.invalid_limit"


class RunPublishFailedError(RunFamilyError):
    """`run.publish_failed`."""

    code: ClassVar[str] = "run.publish_failed"
