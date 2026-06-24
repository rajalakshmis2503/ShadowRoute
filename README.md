# ShadowRoute

## Revealing Hidden Privacy Risks in Fitness Tracking Data

### Overview

ShadowRoute is a privacy risk assessment tool that explores how publicly shared fitness tracking data can unintentionally expose sensitive information about users.

Fitness applications often allow users to share GPS-based activities such as runs, walks, and cycling routes. While this data appears harmless, repeated activity patterns can reveal information about a person's movements, habits, and locations. ShadowRoute demonstrates how these risks can emerge by analysing GPX activity files and identifying potential privacy exposures.

The project was inspired by discussions surrounding location privacy on fitness platforms, particularly the risks associated with publicly visible activity data.

---

## Problem Statement

Location-based fitness data can reveal more than intended.

Repeated routes, recurring activity patterns, and frequently visited locations may allow third parties to infer sensitive information such as:

* Potential residence locations
* Frequently visited places
* Predictable movement patterns
* Activity habits and behaviours

ShadowRoute was developed to assess these risks and promote greater awareness of privacy considerations when sharing fitness activity data online.

---

## Features

### GPX Activity Analysis

Upload GPX activity files and visualise recorded routes on an interactive map.

### Residence Exposure Assessment

Identifies clusters of recurring route endpoints that may indicate locations frequently associated with a user.

### Repeated Route Identification

Detects routes that are repeatedly used across multiple activities.

### Behavioural Pattern Analysis

Examines recurring movement patterns that may contribute to privacy exposure.

### Frequent Location Analysis

Highlights locations that appear consistently across uploaded activities.

### Privacy Exposure Scoring

Calculates an overall privacy exposure score based on identified risk indicators.

### Privacy Recommendations

Provides practical recommendations to help reduce location-based privacy risks.

---

## Technology Stack

* Python
* Streamlit
* Folium
* Pandas
* NumPy
* GPX Parsing Libraries

---

## Example Workflow

1. Upload one or more GPX activity files.
2. Visualise routes on an interactive map.
3. Analyse activity data for privacy risk indicators.
4. Review exposure scores and identified risks.
5. Explore recommended privacy controls.

---

## Key Takeaways

ShadowRoute demonstrates how seemingly harmless fitness tracking data can contribute to unintended privacy exposure.

The objective is not to determine a user's exact home address or identity, but to illustrate how publicly available location data can be analysed to infer sensitive information about movement patterns and frequently visited locations.

This project highlights the importance of:

* Privacy by Design
* Data Minimisation
* User Awareness
* Risk-Based Privacy Assessments

---

## Future Enhancements

* Improved geospatial clustering techniques
* Confidence scoring for location inference
* Privacy zone simulation
* Enhanced reporting and visualisations
* Support for additional activity formats

---

## Disclaimer

ShadowRoute is an educational proof-of-concept developed for cybersecurity and privacy risk analysis purposes. Results are based on pattern analysis and should not be interpreted as definitive identification of any individual, residence, or location.
