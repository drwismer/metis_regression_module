# Project MVP - UFC Scoring

The goal of the project was to create a model that predicted the fight score given fight metrics, sort of an automated judge. I tested a wide variety of regression models, tuning the parameters of each. Below are the testing results for the models that passed cross validation. I considered R-Square, RMSE, and the accuracy of the winner predictions. 

#### Model Performance
I moved three models forward to the testing phase. This visual shows how each performed based on R-Squared, RMSE, and prediction accuracy. 

<img src='images/pic - model performance.png' width=800>

#### Linear Regression Model 
I selected the Linear Regression model (with normalized data) as my winning model. This visual shows the coefficients for the features of the model, and these are very much in line with the prescribed judging criteria hierarchy.

<img src='images/pic - feature coef.png' width=800>

#### Winner Predictions 
This visual shows how well the winning model predicts the winner of a fight. A natural cutoff forms at 9.5 points per round. This is because, generally, one fighter gets 10 points per round and the other fighter gets 9 points per round. As such, the average points per round is 9.5. There are only two fighters in each fight, so if you perform above average, you win. If you perform below average, you lose. This means that, typically, when the predicted per round score and the actual per round score ***fall on the same side of 9.5***, the prediction will be correct.

<img src='images/pic - predictions.png' width=800>
