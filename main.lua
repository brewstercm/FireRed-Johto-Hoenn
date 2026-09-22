-- Native FireRed/LeafGreen API 2 content mod.
local mod = ...

local source = assert(mod:read("data/placements.lua"), "missing data/placements.lua")
local placements = assert(load(source, "@firered_johto_hoenn/placements", "t", {}))()

local function copy(value)
  if type(value) ~= "table" then return value end
  local out = {}
  for k, v in pairs(value) do out[k] = copy(v) end
  return out
end

local function warn(message)
  if mod.log and mod.log.warn then mod.log:warn(message) end
end

local function matchesVanillaExpected(current, expected)
  if type(expected) ~= "table" then return false end
  return current == expected.firered or current == expected.leafgreen
end

-- ---------------------------------------------------------------------------
-- Wild encounter patches
-- ---------------------------------------------------------------------------

local grouped, mapIds, checked = {}, {}, {}
for _, p in ipairs(placements) do
  if not checked[p.species] then
    assert(
      mod.content.pokemon:get(p.species),
      "FRLG species unavailable: " .. p.species
    )
    checked[p.species] = true
  end

  assert(
    type(p.expected) == "table"
      and type(p.expected.firered) == "string"
      and type(p.expected.leafgreen) == "string",
    "missing FRLG vanilla expectations for " .. p.map
  )

  if not grouped[p.map] then
    grouped[p.map] = {}
    mapIds[#mapIds + 1] = p.map
  end
  grouped[p.map][#grouped[p.map] + 1] = p
end
table.sort(mapIds)

local lengths = { land = 12, water = 5, fishing = 10 }

for _, mapId in ipairs(mapIds) do
  local record = mod.content.encounters:get(mapId)
  local patch, valid = {}, type(record) == "table"

  for _, p in ipairs(grouped[mapId]) do
    local area = valid and record[p.terrain]
    local slots = area and area.slots
    local current = slots and slots[p.slot] and slots[p.slot].species

    if type(slots) ~= "table"
        or #slots ~= lengths[p.terrain]
        or not slots[p.slot]
        or not matchesVanillaExpected(current, p.expected) then
      valid = false
      break
    end

    if not patch[p.terrain] then
      patch[p.terrain] = { slots = copy(slots) }
    end
    patch[p.terrain].slots[p.slot].species = p.species
  end

  if valid then
    mod.content.encounters:patch(mapId, patch)
  else
    warn(
      "Skipping incompatible encounter table "
      .. mapId
      .. "; another encounter mod or engine data change may be active"
    )
  end
end

-- ---------------------------------------------------------------------------
-- Pokédex AREA support
--
-- Gen1Recomp currently builds its FRLG Pokédex area index from the imported
-- vanilla encounters.lua snapshot. Encounter registry patches therefore work
-- in-game but are invisible to the Pokédex Area page.
--
-- Replace that one internal rebuild function so it reads the live merged
-- Gen 3 encounter tables instead. This is why the manifest declares the
-- engine_internals permission.
-- ---------------------------------------------------------------------------

local function installPokedexAreaRefresh()
  local okDex, PokedexData = pcall(require, "src.core.game3.pokedex_data")
  if not okDex or type(PokedexData) ~= "table" then
    warn("Could not install Pokédex area refresh")
    return
  end

  local okGroups, mapGroups = pcall(require, "src.import.gba.map_groups_firered")
  local okSections, MapSectionsExtract =
    pcall(require, "src.import.gba.map_sections_extract")

  if not okGroups or type(mapGroups) ~= "table"
      or not okSections or type(MapSectionsExtract) ~= "table" then
    warn("Could not load FRLG map metadata for Pokédex area refresh")
    return
  end

  local function rebuildWildAreas()
    local game = mod.game
    local data = game and game.data
    local encounters = data and data.gen3Encounters
    local areaData = PokedexData._areaData

    if type(encounters) ~= "table" or type(areaData) ~= "table" then
      return false
    end

    local mapsecToArea = areaData.mapsecToArea or {}
    local markers = areaData.markers or {}
    local speciesWildAreas = {}

    local function addSpecies(species, dexArea)
      if not species or species == 0 or not dexArea then return end
      local list = speciesWildAreas[species]
      if not list then
        list = {}
        speciesWildAreas[species] = list
      end
      for _, existing in ipairs(list) do
        if existing == dexArea then return end
      end
      list[#list + 1] = dexArea
    end

    for key, header in pairs(encounters) do
      if type(header) == "table" then
        local gIdx, mIdx = header.mapGroup, header.mapNum

        if not gIdx or not mIdx then
          local gStr, mStr = tostring(key):match("^(%d+):(%d+)$")
          if gStr and mStr then
            gIdx, mIdx = tonumber(gStr), tonumber(mStr)
          end
        end

        if gIdx and mIdx then
          local groups = mapGroups.groups
          local gTable = groups and (groups[gIdx] or groups[gIdx + 1])
          local pretName = gTable
            and gTable.maps
            and (gTable.maps[mIdx + 1] or gTable.maps[mIdx])

          local secIdStr
          if MapSectionsExtract.getInfo then
            local info = MapSectionsExtract.getInfo(nil, pretName)
            secIdStr = info and info.id
          end

          local dexArea = secIdStr and mapsecToArea[secIdStr]
          if not dexArea and pretName then
            local norm = "DEX_AREA_"
              .. tostring(pretName)
                :gsub("^FR_", "")
                :gsub("^SEVII_", "")
                :gsub("([a-z])([A-Z])", "%1_%2")
                :upper()
            if markers[norm] then dexArea = norm end
          end

          if dexArea and (markers[dexArea] or mapsecToArea[secIdStr]) then
            for _, tableKey in ipairs(
              { "land", "water", "rockSmash", "fishing" }
            ) do
              local encounterTable = header[tableKey]
              if encounterTable and encounterTable.slots then
                for _, slot in ipairs(encounterTable.slots) do
                  addSpecies(slot.species, dexArea)
                end
              end
            end
          end
        end
      end
    end

    PokedexData._speciesWildAreas = speciesWildAreas
    return true
  end

  -- PokedexData.init() calls this after area_markers.lua is loaded. Replacing
  -- the builder makes future Pokédex opens use the merged encounter data.
  PokedexData._buildSpeciesWildAreas = rebuildWildAreas

  -- If something initialized the Pokédex before mod loading completed, refresh
  -- it once the game is fully ready and all registry writes have landed.
  if mod.events and mod.events.on then
    mod.events:on("game.ready", function()
      if PokedexData._entries then
        rebuildWildAreas()
      end
    end)
  end
end

installPokedexAreaRefresh()
