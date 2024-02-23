# webservice

## The application features two channels

### First channel: Number guessing
- A game where the user has to guess a number between 1 and 100
- The user will receive feedback according to the last guess whether the target number is higher or lower than the guess
- This way the user can close in on the target number
- If the number is guessed correctly a new number will be chosen automatically and the user can just keep guessing without interruption

### Second channel: Hangman
- The user can play Hangman with a randomly chosen word out of 100
- The user will get feedback after each guess and lives will be deducted if the letter is not included
- If the user tries to guess more than one letter or a letter that was already guessed before he will receive an error and told what he did wrong
- After all lives have run out or the word was fully guessed the user will be informed of the end of the game but a new word will be chosen automatically and the user can just keep guessing without interruption

#### Known Problems
- locally everthing works as intended
- when running the channels on the server we get an error message as soon as anything is input into one of the text fields 
- seemingly the redirect to the show method does not work on the server and we could not figure out why, we tried different versions but none fixed the problem
- our client and the html templates are specifically designed to show our two channels in an appealing manner and variables were given meaningful names, so other channels might not be displayed correctly