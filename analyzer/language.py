from dataclasses import dataclass, field
from collections import Counter
from analyzer.reader import ProjectStructure, FileNode
from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class StackInfo:
    primary_language: str
    languages: dict[str, int]   # extension -> file count
    frameworks: list[str]
    runtime: str | None
    package_manager: str | None
    database_hints: list[str]
    api_hints: list[str]
    test_frameworks: list[str]
    project_type: str            # web, api, bot, cli, library, unknown


LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript (React)",
    ".tsx": "TypeScript (React)",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cpp": "C++",
    ".c": "C",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".vue": "Vue",
    ".svelte": "Svelte",
}

FRAMEWORK_SIGNALS: dict[str, list[str]] = {
    "FastAPI": ["fastapi", "from fastapi"],
    "Flask": ["from flask", "import flask"],
    "Django": ["from django", "import django", "django.conf"],
    "Express": ["require('express')", 'require("express")', "from 'express'", 'from "express"'],
    "React": ["from 'react'", 'from "react"', "import React"],
    "Next.js": ["next/router", "next/image", "getServerSideProps", "getStaticProps"],
    "Vue": ["createApp", "defineComponent", "from 'vue'"],
    "NestJS": ["@nestjs/common", "@nestjs/core", "@Module"],
    "discord.py": ["discord.ext.commands", "from discord", "import discord"],
    "discord.js": ["require('discord.js')", 'from "discord.js"', "new Client("],
    "SQLAlchemy": ["from sqlalchemy", "import sqlalchemy"],
    "Prisma": ["@prisma/client", "PrismaClient"],
    "Mongoose": ["require('mongoose')", 'from "mongoose"'],
    "Pytest": ["import pytest", "from pytest"],
    "Jest": ["describe(", "it(", "test(", "expect("],
    "Tailwind": ["tailwind", "className=\"flex", "className=\"text-"],
    "Pydantic": ["from pydantic", "BaseModel"],
    "Celery": ["from celery", "import celery"],
    "Redis": ["redis", "from redis", "aioredis"],
    "GraphQL": ["graphql", "gql", "GraphQLSchema", "typeDefs"],
}

DB_SIGNALS = {
    "PostgreSQL": ["postgresql://", "psycopg2", "asyncpg", "pg.", "Pool("],
    "MySQL": ["mysql://", "pymysql", "mysql2", "createConnection"],
    "MongoDB": ["mongodb://", "MongoClient", "mongoose"],
    "SQLite": ["sqlite:///", "sqlite3", "better-sqlite3"],
    "Redis": ["redis://", "RedisClient", "createClient("],
    "Supabase": ["supabase", "@supabase/supabase-js"],
    "Firebase": ["firebase-admin", "initializeApp", "getFirestore"],
}

PROJECT_TYPE_SIGNALS = {
    "bot": ["discord", "bot.run", "on_message", "on_ready", "slash_command", "Bot("],
    "api": ["router", "endpoint", "GET /", "POST /", "app.route", "APIRouter"],
    "web": ["html", "template", "render_template", "useState", "useEffect"],
    "cli": ["click", "argparse", "typer", "sys.argv", "commander"],
    "library": ["setup.py", "pyproject.toml", "__all__"],
}


class LanguageDetector:
    def __init__(self, structure: ProjectStructure):
        self.structure = structure

    def detect(self) -> StackInfo:
        lang_counter = Counter[str]()
        all_content = []

        for f in self.structure.files:
            lang = LANGUAGE_MAP.get(f.extension)
            if lang:
                lang_counter[lang] += 1
            if f.content:
                all_content.append(f.content)

        combined = "\n".join(all_content[:200])  # Límite para no saturar memoria

        primary = lang_counter.most_common(1)[0][0] if lang_counter else "Unknown"
        frameworks = self._detect_frameworks(combined)
        dbs = self._detect_signals(combined, DB_SIGNALS)
        project_type = self._detect_project_type(combined)
        runtime, pkg_mgr = self._detect_runtime(primary)
        test_fw = [f for f in frameworks if f in {"Pytest", "Jest"}]
        apis = self._detect_api_patterns(combined)

        return StackInfo(
            primary_language=primary,
            languages=dict(lang_counter),
            frameworks=[f for f in frameworks if f not in {"Pytest", "Jest"}],
            runtime=runtime,
            package_manager=pkg_mgr,
            database_hints=dbs,
            api_hints=apis,
            test_frameworks=test_fw,
            project_type=project_type,
        )

    def _detect_frameworks(self, content: str) -> list[str]:
        found = []
        for fw, signals in FRAMEWORK_SIGNALS.items():
            if any(sig in content for sig in signals):
                found.append(fw)
        return found

    def _detect_signals(self, content: str, signals_map: dict) -> list[str]:
        return [name for name, sigs in signals_map.items() if any(s in content for s in sigs)]

    def _detect_project_type(self, content: str) -> str:
        scores: dict[str, int] = {}
        for ptype, signals in PROJECT_TYPE_SIGNALS.items():
            scores[ptype] = sum(1 for s in signals if s in content)
        if not any(scores.values()):
            return "unknown"
        return max(scores, key=lambda k: scores[k])

    def _detect_runtime(self, primary: str) -> tuple[str | None, str | None]:
        runtimes = {
            "Python": ("Python 3.11+", "pip / pipenv / poetry"),
            "JavaScript": ("Node.js", "npm / yarn / pnpm"),
            "TypeScript": ("Node.js", "npm / yarn / pnpm"),
            "Go": ("Go runtime", "go modules"),
            "Rust": ("Cargo", "cargo"),
            "Java": ("JVM", "Maven / Gradle"),
        }
        entry = runtimes.get(primary)
        if entry:
            return entry
        return None, None

    def _detect_api_patterns(self, content: str) -> list[str]:
        hints = []
        if "REST" in content or "router" in content.lower():
            hints.append("REST API")
        if "graphql" in content.lower() or "typeDefs" in content:
            hints.append("GraphQL")
        if "websocket" in content.lower() or "WebSocket" in content:
            hints.append("WebSocket")
        if "grpc" in content.lower():
            hints.append("gRPC")
        return hints