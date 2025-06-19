from __future__ import annotations

from typing import Any, NamedTuple
import requests
from bs4 import BeautifulSoup
import json
from time import sleep
from random import random

BASE_URL = "https://www.bat.org"
INDEX_URL = f"{BASE_URL}/help/sksp"
OUTPUT = "skills_spells.json"


def get_index() -> list[tuple[str, str]]:
    """
    returns skill and spell names and respective urls from the index page
    """

    response = requests.get(INDEX_URL)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # find all a.boxlink

    skill_links = soup.select("a.boxlink[href^='/help/skill']")
    spell_links = soup.select("a.boxlink[href^='/help/spell']")

    # parse skill/spell names and urls

    skills = [(link.text.strip(), f"{BASE_URL}{link['href']}") for link in skill_links]
    spells = [(link.text.strip(), f"{BASE_URL}{link['href']}") for link in spell_links]

    return skills + spells


# example content
#
# <div id="RightContent">
#   <h1>Spell: Blast vacuum</h1>
#   <p></p>
#   <div class="tabs"></div>
#   <div class="skHeadLeft">Casting time:</div>
#   <div class="skHeadRight">4 rounds</div>
#   <div class="skHeadLeft">Cast type:</div>
#   <div class="skHeadRight">Asphyxiation</div>
#   <div class="skHeadLeft">Damage type:</div>
#   <div class="skHeadRight">Asphyxiation</div>
#   <div class="skHeadLeft">Spell Point Cost:</div>
#   <div class="skHeadRight">170</div>
#   <div class="skHeadLeft">Affecting stats:</div>
#   <div class="skHeadRight">int/wis</div>
#   <div class="skHeadLeft">Reagent:</div>
#   <div class="skHeadRight">Bronze marble</div>
#   <div class="skspDark rounded inline center" style="margin: 2px;width: 711px;padding: 3px 8px;">
#     <span class="bright">Spell Vocals:</span> 'ghht mar nak grttzt'
#   </div>
#   <div class="rounded skspDark inline" style="padding: 3px 8px;">
#     <p>One of the most powerful spells that use air against the target is the spell
# blast vacuum. Similar to the spell chaos bolt, an active pocket of air is sent
# at the target where it is released, sucking all the air around the target
# away. The difference between the two, is that the spell blast vacuum creates a
# much larger and more powerful pocket. When this spell hits the target, the
# pressure outward from the target is so great that the targets outer skin
# actually expands, enough that it can be noticed by the naked eye. Blood vessels
# rupture and can cause open wounds. Some internal organs can also be affected,
# causing great pain.
#     </p>
#   </div>


class Sksp(NamedTuple):
    name: str
    is_skill: bool  # spell: false
    url: str
    params: dict[str, str]
    description: str

    def to_dict(self) -> dict[str, str | bool]:
        return {
            "name": self.name,
            "is_skill": self.is_skill,
            "url": self.url,
            "description": self.description,
            **self.params,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Sksp:
        return cls(
            name=data["name"],
            is_skill=data["is_skill"],
            url=data["url"],
            params={
                k: v
                for k, v in data.items()
                if k not in ["name", "is_skill", "url", "description"]
            },
            description=data["description"],
        )


def get_sksp_page(url: str) -> Sksp:
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # find the main content of the skill page
    content = soup.select_one("div#RightContent")

    if not content:
        raise ValueError(f"Could not find content for URL: {url}")

    # extract the skill name
    name_tag = content.select_one("h1")
    if not name_tag:
        raise ValueError(f"Could not find skill name in content for URL: {url}")

    # remove heading Spell: or Skill:
    name = name_tag.text.strip().replace("Spell: ", "").replace("Skill: ", "")

    is_skill = "skill" in url

    # extract parameters

    params = {}
    for left, right in zip(
        content.select("div.skHeadLeft"), content.select("div.skHeadRight")
    ):
        key = left.text.strip().lower().replace(":", "").replace(" ", "_")
        value = right.text.strip().lower()
        if value != "":
            params[key] = value

    description_tags = content.select("div.skspDark")
    if not description_tags:
        raise ValueError(f"Could not find description in content for URL: {url}")

    if not is_skill and "Spell Vocals:" in description_tags[0].text:
        vocals = (
            description_tags.pop(0)
            .text.strip()
            .replace("Spell Vocals: ", "")
            .strip("'")
        )
        params["spell_vocals"] = vocals

    description = description_tags[0].text.strip().replace("\n", " ")

    return Sksp(
        name=name.lower(),
        is_skill=is_skill,
        url=url,
        params=params,
        description=description,
    )


def load_output() -> dict[str, Sksp]:
    try:
        with open(OUTPUT, "r", encoding="utf-8") as f:
            data = f.read()
            return {k: Sksp.from_dict(v) for k, v in json.loads(data).items()}
    except FileNotFoundError:
        return {}


if __name__ == "__main__":
    print("Staring skill and spell scraper")

    parsed_sksps = load_output()
    print(f"Loaded {len(parsed_sksps)} skills and spells")

    name_urls = get_index()
    print(f"Found {len(name_urls)} skills and spells in the index")

    for name, url in name_urls:
        if name.lower() in parsed_sksps:
            continue

        sksp = get_sksp_page(url)
        parsed_sksps[name.lower()] = sksp
        print(f"Loaded {sksp.name}")
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(
                {k: v.to_dict() for k, v in parsed_sksps.items()},
                f,
                ensure_ascii=False,
                indent=4,
            )

        # sleep a random time between 0 and 2 seconds to avoid hammering the server
        sleep(0.5 + 2.5 * random())
