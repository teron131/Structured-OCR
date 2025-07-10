TEXT_EXTRACTION_PROMPT = """The given image shows a screenshot of a game scoreboard with two teams: Heroes and Villains. The given text is the OCR text results for reference. With a holistic overview of the layout, extract and organize the content into a structured JSON format following these guidelines:

1. Identify the two teams ('Heroes' and 'Villains') as shown at the top of each column.
2. Identify the highlighted player ("me") and assign to the 'me' field.
3. For each player, extract the following fields:
   - name: string, the player's displayed name.
   - level: int, the player's level, where MAX is 1000.
   - kills: int, number of kills.
   - assists: int, number of assists.
   - deaths: int, number of deaths.
   - kd: float, K/D ratio.
   - score: int, the player's score.
4. Group players into:
   - 'me': the player in yellow highlight.
   - 'squad': list of players in green highlight.
   - 'enemies': list of players on the opposing side.
5. Ensure numeric values are parsed correctly (e.g., decimals to floats).
6. Output ONLY the JSON object conforming to the Pydantic schema for Match."""


CHECKER_PROMPT = """Be a rigorous and strict checker and grade whether the following criteria are met on a scale of 0 to 10 for OCR extraction of the game scoreboard screenshot. 10 means perfect extraction. If criteria are not met, provide detailed reasons.

Verification Checklist:
1. Team Names:
   - Verify team names 'Heroes' and 'Villains' are correctly identified.
   - Indistinguishabilities such as 'I' and 'l', 'O' and '0', 'S' and '5', 'Z' and '2', are acceptable.
2. Highlighted Player:
   - Confirm the 'me' player is correctly identified.
3. Player Data Accuracy:
   - Check each player's name, level, kills, assists, deaths, K/D ratio, and score are accurately extracted.
4. Grouping:
   - Ensure teammates and enemies are correctly grouped relative to 'me'."""
