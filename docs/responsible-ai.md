# Responsible AI notes

## Where the data comes from

The benchmark uses FreshRetailNet-50K by Dingdong-Inc, published on Hugging Face under CC BY 4.0, which allows reuse with credit. The README and the results page credit it. Its store and product IDs are encoded and its sales are normalised, so Binless never shows a real product name next to its figures.

The live order page uses a shop I simulate in `forecasting/simulation.py`. Its name, products, prices, costs and sales are invented. Every page that shows them says so.

## Personal data

Binless holds no customer personal data. The forecasts work from daily sales totals per product, weather and calendar flags. Nothing about who bought what is needed or stored. The only personal data in the system today would be a login for the Django admin, which isn't exposed in Phase 1.

## Risk under the EU AI Act

My reading is that Binless falls in the minimal-risk group. It recommends stock quantities for a shop. It doesn't make decisions about people, so it isn't in any of the high-risk areas listed in Annex III (such as employment, credit or access to services), and it isn't a prohibited practice. Phase 1 has no chatbot and no generated text. When I add LLM-written explanations in Phase 2, they will be labelled as AI-generated, which is what Article 50's transparency rules ask for. This is my own reading, not legal advice.

## Human oversight

The shop owner stays in charge of every order:

- each recommended quantity is an editable field, so the owner can change any line
- the slider lets the owner decide how much an empty shelf matters compared with waste, instead of the model deciding
- each line shows the forecast range and the two strongest reasons behind it, so a surprising number can be checked against what the owner knows

Logging overrides and measuring how often recommendations are accepted is planned for Phase 2.

## Security

- The Django secret key and the database URL live in AWS SSM Parameter Store as encrypted parameters. The app reads them at start-up, and they never appear in git, the images or the SAM template.
- DEBUG is off unless an environment variable turns it on, and the app only answers on the hosts it expects.
- Each Lambda's role can read only the two parameters it needs, and the batch can read only the model bucket. The bucket blocks public access.
- I deploy as an IAM user with MFA and short-lived credentials, not as the AWS root user.

## Limitations

- The simulated shop is not evidence that Binless works in a real shop. The benchmark on FreshRetailNet-50K is the evidence, and it comes from one Chinese retailer's data, so results in an Irish shop may differ.
- The cost assumptions behind the order rule are mine, not any retailer's.
- The model card lists the forecasting limitations, including the low bias on the held-out week and the upper quantiles covering too rarely.
