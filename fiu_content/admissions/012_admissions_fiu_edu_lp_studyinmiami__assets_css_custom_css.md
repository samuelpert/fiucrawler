---
url: https://admissions.fiu.edu/lp/studyinmiami/_assets/css/custom.css
site: admissions
crawled_at: 2025-05-12T15:10:28.196569
title: None
---

# https://admissions.fiu.edu/lp/studyinmiami/_assets/css/custom.css

```
body, html {
  font-size: 18px;
}
.wide > .row {
  max-width: 80rem;
}
.note {
  font-size: 0.88888889rem;
}
.center {
  text-align: center;
}
form input,
form textarea,
form select {
  border-radius: 5px !important;
  margin: 0 !important;
  padding: 0.5rem 0.88888889rem !important;
  height: auto !important;
  font-size: 0.88888889rem !important;
  line-height: 1.5;
  color: #333 !important;
}
form .button {
  font-size: 0.88888889rem !important;  
}
::placeholder {
  opacity: 0.9;
}
#floating-apply {
  z-index: 99;
  position: fixed;
  left: 1rem;
  bottom: 1rem;
}
@media (min-width: 641px) {
  #floating-apply {
    left: 2rem;
    bottom: 2rem;
  }
}
#form-message {
	position: fixed;
	z-index: 100;
  left: 50%;
  width: 500px;
  top: 2rem;
  margin-left: -250px;
	margin-right: 1rem;
	transform: translateY(-120%);
	transition: .2s ease-in-out;
}
@media (max-width: 550px) {
  width: 80%;
  left: 10%;
}
#form-message.in {
	transform: translateY(0);
}
/* Panels */
.panel.callout.green {
  border-left: 7px solid #43ac6a;
  box-shadow: none;
}
/* Banner */
#banner,
#banner-video {
  z-index: 99;
  outline: 1px solid rgba(256,256,256,0.8);
  outline-offset: -1.88888889rem;
}
#banner .headline-container,
#banner-video .headline-container {
  padding: 0;
  background: #081E3FD6 0% 0% no-repeat padding-box;
}
#banner .row,
#banner-video .row {
  max-width: 100%;
}
#banner .row .columns,
#banner-video .row .columns {
  padding: 0;
}
#banner.banner-flex .content-flex .content,
#banner-video.banner-flex .content-flex .content {
  padding: 5rem;
  width: 100%;
  text-align: center;
}
#banner h1,
#banner-video h1 {
  position: static;
  margin-bottom: 1.5rem;
  transform: none;
}
.custom-banner-wrapper .content-area p,
.custom-banner-wrapper .content-area li {
  font-size: 1.11111111rem;  
}
.custom-banner-wrapper .content-wrapper > *:last-child {
  margin-bottom: 0;
}
#banner .custom-banner-wrapper .display-text--large,
#banner-video .custom-banner-wrapper .display-text--large {
  font-size: 3.44444444rem;
  text-shadow: 0px 3px 6px #0000004D;
}
#banner .custom-banner-wrapper .display-text--large em,
#banner-video .custom-banner-wrapper .display-text--large em {
  font-style: normal;
}
.custom-banner-wrapper .cta-link-primary,
.custom-banner-wrapper .cta-link-primary::after,
.custom-banner-wrapper .cta-link-primary:focus,
.custom-banner-wrapper .cta-link-primary:focus::after {
  color: #00FFFF !important;
}
.custom-banner-wrapper .form-area {
  margin-top: 2.5rem;
}
.custom-banner-wrapper .form-area .form-wrapper > *:last-child {
  margin-bottom: 0;
}
.custom-banner-wrapper .form-area h3 {
  font-size: 1.11111111rem;
  font-weight: 700;
}
.custom-banner-wrapper .form-area form {
  display: block;
  margin-bottom: 1.5rem;
}
.custom-banner-wrapper .form-area .form-field {
  margin-bottom: 1rem;
}
#banner-video form button {
  position: static;
  border: none;
  border-radius: 5px;
  margin: 0;
  width: auto;
  height: auto;
  transform: none;
  transition: opacity .2s ease;
  min-width: 120px;
}
#banner-video form button:hover {
  opacity: 0.9;
}
#banner-video form button.button--gold {
  background-color: #FC0;
  
}
@media (min-width: 641px) and (max-width: 1024px) {
  /* Has Form */
  .custom-banner-wrapper .form-area form {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  .custom-banner-wrapper .form-area .form-field {
    margin: 0;
    width: calc(50% - 0.25rem);
  }
  .custom-banner-wrapper .form-area .form-field.center {
    margin-top: 1rem;
    width: 100%;
  }
  .custom-banner-wrapper .form-area textarea {
    min-height: 0 !important;
    height: 44px !important;
  }
}
@media (min-width: 1025px) {
  #banner .headline-container,
  #banner-video .headline-container {
    background: #081E3FA6 0% 0% no-repeat padding-box;
  }
  #banner.banner-flex .content-flex .content,
  #banner-video.banner-flex .content-flex .content {
    padding: 0;
    text-align: left;
  }
  .custom-banner-wrapper {
    display: flex;
    justify-content: center;
    width: 100%;
  }
  .custom-banner-wrapper .content-area {
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    font-size: 1.11111111rem;
    min-height: 750px;
    width: calc(100% - 444px);
  }
  .short .custom-banner-wrapper .content-area {
    min-height: 550px;  
  }
  .custom-banner-wrapper .content-wrapper {
    width: 100%;
    max-width: 690px;
  }
  .short .custom-banner-wrapper .content-wrapper {
    padding-top: 8rem;
  }
  .custom-banner-wrapper .banner-logo {
    position: absolute;
    left: 0;
    top: 5rem;
    padding-left: 4rem;
    padding-right: 3rem;
    width: 100%;
    text-align: center;
  }
  /* With Form */
  #banner.has-form {
    background: transparent !important;
  }
  #banner.has-form::before {
    content: '';
    z-index: -1;
    background: url(../images/banner-homepage.jpg) 45% 0 no-repeat;
    background-size: cover;
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: calc(100% - 444px);
  }
  #banner-video.has-form .video-wrapper {
    width: calc(100% - 444px);
  }
  .has-form .custom-banner-wrapper .content-wrapper {
    padding-left: 4rem;
    padding-right: 3rem;
  }
  .custom-banner-wrapper .form-area {
    display: flex;
    margin-top: 0;
    padding: calc(2rem - 3px);
    padding-left: 0;
    min-width: 444px;
    background-color: #081E3F;
    width: 30%;
  }
  .custom-banner-wrapper .form-area .form-wrapper {
    display: flex;
    flex-wrap: wrap;
    flex-direction: column;
    justify-content: center;
    border: 1px solid rgba(256,256,256,0.8);
    border-left: 0;
    padding: 1.5rem 3rem;
    text-align: center;
  }
  .custom-banner-wrapper .form-area form {
    display: block;
  }
}
@media (max-width: 567px) {
  #banner, #banner-video {
    outline-offset: -.9375rem;
  }
  #banner.banner-flex .content-flex .content, 
  #banner-video.banner-flex .content-flex .content {
    padding: 3rem;  
  }
  #banner-video.banner-flex .content-flex .content {
    padding-bottom: 5rem;
  }
  #banner .custom-banner-wrapper .display-text--large, 
  #banner-video .custom-banner-wrapper .display-text--large {
    font-size: 2.5rem;  
  }
  .custom-banner-wrapper .form-area {
    margin-top: 1.5rem;
  }
  #banner-video button {
    bottom: 2.5rem;
  }
}
/* Photo Collage */
@media (min-width: 641px) {
  .content-block--full-width.module-photo-collage .small-12 {
    max-width: 1366px !important;
    padding-left: 5px;
    padding-right: 5px;
  }
  .photo-collage {
    display: flex;
    flex-wrap: nowrap;
    gap: 5px;
    height: 85vh;
    min-height: 600px;
    max-height: 1214px;
  }
  .photo-collage [class^="column-"] {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }
  .photo-collage .column-1 {
    width: 37.408492%;
  }
  .photo-collage .column-2 {
    width: 62.225476%;
  }
  .photo-collage [class^="item"] {
    position: relative;
    flex-grow: 1;
    width: 100%;
    overflow: hidden;
  }
  .photo-collage .item-1 {
    height: 26.688633%;
  }
  .photo-collage .item-2 {
    height: 38.22075783%;
  }
  .photo-collage .item-3 {
    height: 35.09060956%;
  }
  .photo-collage .item-4 {
    height: 38.22075783%;
  }
  .photo-collage .item-5 {
    height: 33.93739703%;
  }
  .photo-collage .item-6 {
    height: 27.84184514%;
    width: 22.986823%;
  }
  .photo-collage .item-7 {
    height: 27.84184514%;
    width: 38.872621%;
  }
  .photo-collage [class^="item"] > img {
    position: absolute;
    object-fit: cover;
    object-position: center;
    height: 100%;
    width: 100%;
    transition: all .2s ease;
  }
  .photo-collage .item-1 > img {
    object-position: 50% 80%;
  }
  .photo-collage .item-2 > img {
    object-position: 50% 80%;
  }
  .photo-collage .item-3 > img {
    object-position: bottom;
  }
  .photo-collage .item-4 > img {
    object-position: 50% 30%;
  }
  .photo-collage .item-5 > img {
    object-position: 50% 15%;
  }
  .photo-collage [class^="item"] .text {
    background-color: #000000;
    position: absolute;
    display: flex;
    padding: 2rem;
    height: 100%;
    width: 100%;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: #fff;
    opacity: 0;
    transition: all .3s ease;
  }
  .photo-collage [class^="item"] .text p {
    font-weight: 700;
    position: relative;
    transition: all .2s ease;
    white-space: nowrap;
  }
  .photo-collage [class^="item"] .text p::before,
  .photo-collage [class^="item"] .text p::after {
    content: '';
    position: absolute;
    height: 2px;
    width: 202px;
    background-color: #fff;
    top: 0.91666667rem;
    left: 50%;
    margin-left: -101px;
    transition: all .2s ease;
  }
  .photo-collage [class^="item"] .text p::after {
    top: auto;
    bottom: 0.91666667rem;
  }
  .photo-collage [class^="item"]:hover .text,
  .photo-collage [class^="item"]:focus .text{
    opacity: 1;
    background-color: #000000A6;
  }
  .photo-collage [class^="item"]:hover .text p::before,
  .photo-collage [class^="item"]:focus .text p::before {
    top: -0.91666667rem;
  }
  .photo-collage [class^="item"]:hover .text p::after,
  .photo-collage [class^="item"]:focus .text p::after {
    bottom: -0.91666667rem;
  }
  .photo-collage [class^="item"]:hover > img,
  .photo-collage [class^="item"]:focus > img {
    transform: scale(1.2);
  }
}
@media (min-width: 1366px) {
  .photo-collage [class^="item"]:hover .text p,
  .photo-collage [class^="item"]:focus .text p {
    font-size: 1.66666667rem;
  }
}
@media (max-width: 640px) {
  .module-photo-collage.content-block--full-width .row .small-12 {
    padding-left: .9375rem;
    padding-right: .9375rem;
  }
  .module-photo-collage [class^="item"] {
    position: relative;
    padding-top: 66.66666667%;
    width: 100%;
  }
  .module-photo-collage [class^="item"] img {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: bottom;
  }
  .module-photo-collage [class^="item"] p {
    position: absolute;
    left: 0;
    bottom: 0;
    margin: 0;
    padding: .9375rem;
    width: 100%;
    font-size: 0.88888889rem;
    font-weight: 700;
    background: #fff;
  }
  .module-photo-collage [class^="item"] br {
    display: none;
  }
}
@media (max-width: 480px) {
  .module-photo-collage [class^="item"] {
    padding-top: 100%;  
  }
}
/* Thumbnail Grid Wrapper */
@media (min-width: 641px) and (max-width: 1024px) {
  .thumb-grid.flex-cards.three-columns>li {
    flex: unset;
    width:calc(33% - 0.6rem) !important; 
  }
}
@media (max-width: 640px) {
  .thumb-grid .thumb-grid-wrapper {
    height: 400px;
    overflow: hidden;
  }
  .thumb-grid .thumb-grid-wrapper img {
    position: absolute;
    object-fit: cover;
    object-position: 30%;
    top: 0;
    left: 0;
    height: 100%;
    width: 100%;
  }
}
/* Module: Checklist */
.module--checklist {
  padding-top: 1.5rem;
}
.module--checklist .box {
  border: 1px solid #E6E6E6;
  border-radius: 8px;
  padding: 2.2222rem;
  background-color: #fff;
}
.module--checklist .box + .box {
  margin-top: 2rem;  
}
.module--checklist .related-content {
  border: 0;
  padding: 0;
  background-color: transparent;
}
.module--checklist .related-content h3 {
  font-size: 1rem;
}
.module--checklist .related-content table caption {
  font-weight: 500;
  margin-bottom: 0.5rem;
  text-align: left;
}
.module--checklist .related-content .form-field + .form-field {
  margin-top: 0.5rem;
}
.module--checklist .related-content form button {
  margin-top: 0.5rem;
}
@media (max-width: 1024px) {
  .module--checklist > .row > .columns {
    width: 100%;
    float: none;
  }
  .module--checklist .related-content {
    padding: 2.2222rem;
  }
}
@media (max-width: 1024px) and (min-width: 800px) {
  .module--checklist .medium-8 {
    display: flex;
    flex-wrap: wrap;
    gap: 2rem;
  }
  .module--checklist .box {
    width: calc(50% - 2rem);
  }
  .module--checklist .box + .box {
    margin-top: 0;
  }
}
.module--checklist .related-content form {
  margin-bottom: 1rem;
}
@media (max-width: 640px) {
  .module--checklist .box {
    padding: 1.5rem;
  }
  .module--checklist .box + .box {
    margin-top: .9375rem;
  }
  .module--checklist .related-content {
    padding: 1.5rem;
    margin-top: 0;
  }
}
```


