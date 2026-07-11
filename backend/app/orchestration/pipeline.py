from dataclasses import dataclass, field
from enum import Enum


class InvestigationType(str, Enum):
    EMAIL = "email"
    USERNAME = "username"
    DOMAIN = "domain"
    PHONE = "phone"
    FULL = "full"


@dataclass
class PipelineStep:
    tool: str
    target: str
    depends_on: list[str] = field(default_factory=list)
    kwargs: dict = field(default_factory=dict)


@dataclass
class PipelinePlan:
    seed: str
    type: InvestigationType
    steps: list[PipelineStep] = field(default_factory=list)


class PipelineBuilder:
    def build(self, seed: str, type: InvestigationType) -> PipelinePlan:
        plan = PipelinePlan(seed=seed, type=type)

        if type == InvestigationType.EMAIL:
            plan.steps = self._build_email_pipeline(seed)
        elif type == InvestigationType.USERNAME:
            plan.steps = self._build_username_pipeline(seed)
        elif type == InvestigationType.DOMAIN:
            plan.steps = self._build_domain_pipeline(seed)
        else:
            plan.steps = self._build_email_pipeline(seed)

        return plan

    def _build_email_pipeline(self, email: str) -> list[PipelineStep]:
        domain = email.split("@", 1)[-1] if "@" in email else email
        username = email.split("@", 1)[0] if "@" in email else email

        return [
            # Phase 1: Email-specific checks (parallel)
            PipelineStep(tool="holehe", target=email),
            PipelineStep(tool="ghunt", target=email),
            PipelineStep(tool="h8mail", target=email),
            # Phase 2: Domain recon (runs after email phase)
            PipelineStep(tool="theHarvester", target=domain, kwargs={"domain": domain}, depends_on=[]),
            PipelineStep(tool="waybackpy", target=domain),
            # Phase 3: Username expansion
            PipelineStep(tool="sherlock", target=username, depends_on=[]),
            PipelineStep(tool="maigret", target=username, depends_on=[]),
        ]

    def _build_username_pipeline(self, username: str) -> list[PipelineStep]:
        return [
            PipelineStep(tool="sherlock", target=username),
            PipelineStep(tool="maigret", target=username),
            PipelineStep(tool="socid_extractor", target=username),
            PipelineStep(tool="instaloader", target=username),
            PipelineStep(tool="snscrape", target=username, kwargs={"platform": "twitter"}),
            PipelineStep(tool="snscrape", target=username, kwargs={"platform": "reddit"}),
        ]

    def _build_domain_pipeline(self, domain: str) -> list[PipelineStep]:
        return [
            PipelineStep(tool="theHarvester", target=domain, kwargs={"domain": domain}),
            PipelineStep(tool="emailfinder", target=domain, kwargs={"domain": domain}),
            PipelineStep(tool="censys", target=domain),
            PipelineStep(tool="shodan", target=domain),
            PipelineStep(tool="waybackpy", target=domain),
        ]
