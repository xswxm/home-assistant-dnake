import aiofiles
import json
from typing import Dict

import logging
_LOGGER = logging.getLogger(__name__)

async def load_json(filename: str) -> Dict[str, str]:
    try:
        async with aiofiles.open(filename, mode='r', encoding='utf-8') as file:
            contents = await file.read()
            data = json.loads(contents)
            _LOGGER.debug(f'Loaded data from {filename}: {data}')
            return data
    except FileNotFoundError:
        _LOGGER.error(f'{filename} not found.')
        return {}
    except json.JSONDecodeError:
        _LOGGER.error(f'Failed to decode JSON from {filename}.')
        return {}

async def save_json(result: Dict[str, str], filename: str) -> None:
    if not result:
        return
    async with aiofiles.open(filename, mode='w', encoding='utf-8') as file:
        await file.write(json.dumps(result, ensure_ascii=False, indent=4))
    
    _LOGGER.debug(f'Result saved as {filename}.')