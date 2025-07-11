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
   - 'me': the player in yellow highlight as in squad, or white as solo.
   - 'squad': list of players in green highlight.
   - 'enemies': list of players on the opposing side.
5. Ensure numeric values are parsed correctly (e.g., decimals to floats)."""


CHECKER_PROMPT = """You are a meticulous quality assurance checker evaluating OCR extraction results from a game scoreboard screenshot. Rate each criterion on a scale of 0-10 where:
- 10: Perfect extraction with no errors
- 8-9: Minor errors that don't affect core data integrity
- 6-7: Some errors present but main information is extractable
- 4-5: Significant errors affecting data reliability
- 2-3: Major extraction failures with substantial missing/incorrect data
- 0-1: Complete failure to extract meaningful information

Provide specific scores and detailed reasoning for each criterion:

1. TEAM NAMES (0-10):
   - Verify both team names 'Heroes' and 'Villains' are correctly identified
   - Check proper capitalization and spelling
   - Common OCR confusions are acceptable: 'I'/'l', 'O'/'0', 'S'/'5', 'Z'/'2'
   - Deduct points for missing teams, wrong names, or critical misspellings

2. HIGHLIGHTED PLAYER IDENTIFICATION (0-10):
   - Confirm the 'me' player (yellow highlight as in squad, or white as solo) is correctly identified and placed
   - Verify the player exists in the extracted data with complete information
   - Check that highlighting detection worked properly
   - Deduct points if wrong player identified as 'me' or missing entirely

3. PLAYER DATA ACCURACY (0-10):
   - Evaluate extraction precision for ALL players across these fields:
     * name: Player's displayed username (string)
     * level: Numeric level (0-1000, integer, MAX is 1000)
     * kills: Kill count (integer)
     * assists: Assist count (integer) 
     * deaths: Death count (integer)
     * kd: Kill/Death ratio (float, typically 0.00-99.99)
     * score: Total match score (integer)
   - Check for missing players, incorrect values, wrong data types
   - Verify numerical accuracy and proper parsing of decimals, zeroes can be obmitted such as 0.10 & 0.1 are interchangeable
   - Assess completeness across all visible players in the screenshot

4. PLAYER GROUPING (0-10):
   - Validate correct assignment of players to categories:
     * 'me': Single yellow-highlighted player
     * 'squad': Green-highlighted teammates (if any)
     * 'teammates': All players on same side as 'me' (excluding 'me')
     * 'enemies': All players on opposing team
   - Ensure no player appears in multiple categories inappropriately
   - Check that team affiliations match the visual layout
   - Verify total player count matches screenshot

For each criterion below the threshold, provide:
- Specific examples of errors found
- Expected vs. actual values
- Impact on data usability
- Suggestions for improvement

Be exceptionally thorough in your analysis and err on the side of being more critical rather than lenient."""
