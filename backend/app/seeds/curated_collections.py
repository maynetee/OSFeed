from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.collection import Collection

CURATED_COLLECTIONS = [
    {
        "name": "Ukraine & Eastern Europe",
        "description": (
            "Live coverage of the Ukraine conflict and Eastern European geopolitics. "
            "Includes official Ukrainian military channels, independent conflict monitors, "
            "and regional news sources."
        ),
        "region": "Europe",
        "topic": "Conflict",
        "curator": "OSFeed",
        "curated_channel_usernames": [
            "ukrainenowenglish", "DeepStateUA", "operativnoZSU", "UkrainianLand",
            "EuromaidanPR", "militarylandnet", "flashnewsua", "TpyxaNews",
            "KyivIndependent", "nexaboronka", "saboronka", "noaboronka",
            "ukikiepravda_eng", "ukraine_avdet", "UkraineNow",
        ],
    },
    {
        "name": "Middle East & North Africa",
        "description": (
            "Coverage of conflicts, politics, and security developments across the MENA "
            "region. Includes channels covering Syria, Iraq, Yemen, Libya, and the "
            "broader Arab world."
        ),
        "region": "Middle East",
        "topic": "Conflict",
        "curator": "OSFeed",
        "curated_channel_usernames": [
            "SyrianObservatory", "Iraq_Mokhtar", "YemenPress", "LibyaReview",
            "MiddleEastEye_channel", "AlJazeeraChannel", "ArabNewsBrk",
            "GazaNewsNow", "LebanonTimes", "IranIntl_En",
        ],
    },
    {
        "name": "Cyber Threat Intelligence",
        "description": (
            "Curated channels tracking cyber threats, data breaches, vulnerability "
            "disclosures, and threat actor activity. Essential for cybersecurity "
            "professionals and SOC teams."
        ),
        "region": "Global",
        "topic": "Cybersecurity",
        "curator": "OSFeed",
        "curated_channel_usernames": [
            "caboronka", "daboronka", "eaboronka", "RansomwareNews",
            "cyberundergroundfeed", "DarkWebInformer", "vaboronka",
            "HackerNewsOnline", "BleepingComputerCh", "CVEnews",
        ],
    },
    {
        "name": "Russian Independent Media",
        "description": (
            "Independent and opposition-leaning Russian-language media outlets "
            "providing alternative perspectives on Russian politics, society, "
            "and the war in Ukraine."
        ),
        "region": "Russia & CIS",
        "topic": "Politics",
        "curator": "OSFeed",
        "curated_channel_usernames": [
            "medaboronka", "novaya_gazeta", "echomskru", "tvaboronka",
            "CurrentTimeTVnews", "SotaVision", "the_ins_ru",
            "AvtozakLIVE", "OVDinfo", "MBKhMedia",
        ],
    },
    {
        "name": "Africa Security Monitor",
        "description": (
            "Tracking security, conflicts, and political developments across "
            "Sub-Saharan Africa. Covers the Sahel region, East Africa, and "
            "Southern Africa."
        ),
        "region": "Africa",
        "topic": "Security",
        "curator": "OSFeed",
        "curated_channel_usernames": [
            "AfricaDefenseF", "SahelSecurityM", "EthiopiaInsider",
            "MozambiqueConflict", "NigeriaSecUpdate", "CongoResearch",
            "SomaliaSecurity", "SudanWarUpdate",
        ],
    },
    {
        "name": "Asia-Pacific Geopolitics",
        "description": (
            "Monitoring strategic developments in the Asia-Pacific region including "
            "South China Sea tensions, Korean Peninsula, Taiwan Strait, and "
            "Indo-Pacific security architecture."
        ),
        "region": "Asia-Pacific",
        "topic": "Geopolitics",
        "curator": "OSFeed",
        "curated_channel_usernames": [
            "SCSAnalysis", "NKoreaWatch", "TaiwanStraitsObs",
            "IndoPacificBrief", "ChinaDigitalTimes", "SCMP_News",
            "JapanTimesAlert", "AsiaSentinel",
        ],
    },
    {
        "name": "Latin America Watch",
        "description": (
            "Coverage of political instability, organized crime, migration, "
            "and social movements across Central and South America."
        ),
        "region": "Americas",
        "topic": "Politics",
        "curator": "OSFeed",
        "curated_channel_usernames": [
            "VenezuelaReport", "ColombiaConflict", "MexicoSecurity",
            "BrazilPulse", "CubaLibre_News", "ArgentinaAlert",
            "CentralAmericaObs",
        ],
    },
    {
        "name": "European Security & Defense",
        "description": (
            "NATO and European defense developments, military exercises, arms "
            "transfers, and security policy debates across the European continent."
        ),
        "region": "Europe",
        "topic": "Defense",
        "curator": "OSFeed",
        "curated_channel_usernames": [
            "NATOpress", "EUDefenseWatch", "BalticSentinel",
            "PolandDefense", "NordicMonitor", "BalkansInsider",
            "UKDefenceJournal", "FranceArmed",
        ],
    },
    {
        "name": "Global Terrorism Monitor",
        "description": (
            "Tracking terrorist activities, radicalization trends, and "
            "counter-terrorism operations worldwide. Includes channels from "
            "multiple regions and analytical sources."
        ),
        "region": "Global",
        "topic": "Terrorism",
        "curator": "OSFeed",
        "curated_channel_usernames": [
            "SITEIntelGroup", "CTCWestPoint", "ICTAnalysis",
            "TerrorismMonitor", "JihadWatch_ch", "RadicalizationStudy",
            "ISISWatchdog",
        ],
    },
    {
        "name": "Energy & Commodities Intelligence",
        "description": (
            "Monitoring global energy markets, pipeline politics, sanctions "
            "impacts, and commodity supply chain disruptions that affect "
            "geopolitical dynamics."
        ),
        "region": "Global",
        "topic": "Economy",
        "curator": "OSFeed",
        "curated_channel_usernames": [
            "OPECwatch", "EnergyIntelReport", "GasMarketAnalyst",
            "OilPriceAlert", "SanctionsTracker", "CommodityPulse",
            "CriticalMinerals",
        ],
    },
    {
        "name": "Humanitarian & Migration",
        "description": (
            "Tracking humanitarian crises, refugee movements, disaster response, "
            "and aid operations globally. Includes UNHCR, ICRC, and independent "
            "monitor channels."
        ),
        "region": "Global",
        "topic": "Humanitarian",
        "curator": "OSFeed",
        "curated_channel_usernames": [
            "UNHCRnews", "ICRCnews", "MSF_updates",
            "MigrationWatch_EU", "RefugeeInfoHub", "HumanitarianPulse",
            "DisasterAlert_ch",
        ],
    },
    {
        "name": "Disinformation & Info Ops",
        "description": (
            "Channels dedicated to tracking disinformation campaigns, information "
            "operations, media manipulation, and fact-checking across multiple "
            "languages and regions."
        ),
        "region": "Global",
        "topic": "Information",
        "curator": "OSFeed",
        "curated_channel_usernames": [
            "DisinfoWatch", "EUvsDisinfo_ch", "FactCheckHub",
            "MediaManipAlert", "BotSentinel_ch", "PropagandaMonitor",
            "InfoOpsTracker",
        ],
    },
]


async def seed_curated_collections(db: AsyncSession):
    """Seed curated collections. Idempotent - skips if already exist."""
    for data in CURATED_COLLECTIONS:
        existing = await db.execute(
            select(Collection).where(
                Collection.name == data["name"],
                Collection.is_curated.is_(True),
            )
        )
        if existing.scalar_one_or_none():
            continue
        collection = Collection(
            name=data["name"],
            description=data["description"],
            region=data["region"],
            topic=data["topic"],
            curator=data["curator"],
            is_curated=True,
            curated_channel_usernames=data["curated_channel_usernames"],
            last_curated_at=datetime.now(timezone.utc),
        )
        db.add(collection)
    await db.commit()
