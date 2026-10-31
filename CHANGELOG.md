# Changelog

## [0.3.0](https://github.com/OpenReloading/AutoLever/compare/v0.2.0...v0.3.0) (2026-10-31)


### Features

* **docs:** header and footer in the navy and orange look ([#103](https://github.com/OpenReloading/AutoLever/issues/103)) ([3ddecc7](https://github.com/OpenReloading/AutoLever/commit/3ddecc7c4b23dded4ab321d52daf3150e9fb05ce))
* **docs:** home page hero, status band and fact strip ([#104](https://github.com/OpenReloading/AutoLever/issues/104)) ([75886cb](https://github.com/OpenReloading/AutoLever/commit/75886cbfc66612e122abd9db5d8514708c7d99d0))
* **docs:** home page sections as cards, step row and change-it columns ([#105](https://github.com/OpenReloading/AutoLever/issues/105)) ([98a8cfa](https://github.com/OpenReloading/AutoLever/commit/98a8cfa25c3ce902a2e3b5cef3769c0fe450b31c))
* **docs:** navy and orange tokens, amber safety panel and social card ([#102](https://github.com/OpenReloading/AutoLever/issues/102)) ([daf026f](https://github.com/OpenReloading/AutoLever/commit/daf026f532adc39a1fdfa10f3c1fb0e25f6cd364))
* **docs:** pinch zoom on the boards with BuildGuide 0.1.4 ([#114](https://github.com/OpenReloading/AutoLever/issues/114)) ([3565a36](https://github.com/OpenReloading/AutoLever/commit/3565a361a16ceb0be53d8d5346bc407dadf3399b))
* **docs:** step label, title and token colours on the BOM, wiring and tubing pages ([#106](https://github.com/OpenReloading/AutoLever/issues/106)) ([4f66dce](https://github.com/OpenReloading/AutoLever/commit/4f66dce53988d08d92737ce06bb75fcefeefe8a4))


### Bug Fixes

* **docs:** 44 px header buttons, search field and card links, checked at 390 and 1440 px ([#107](https://github.com/OpenReloading/AutoLever/issues/107)) ([ca8f986](https://github.com/OpenReloading/AutoLever/commit/ca8f986efb1eaf5622de82b962ef63ccbd2696f1))
* **docs:** give the progress buttons 12 px text and 44 px height at every width ([#127](https://github.com/OpenReloading/AutoLever/issues/127)) ([061811e](https://github.com/OpenReloading/AutoLever/commit/061811eb4e25800e88be5594d76822f2e841c3c5))
* **docs:** underline links in running text ([#115](https://github.com/OpenReloading/AutoLever/issues/115)) ([b38b842](https://github.com/OpenReloading/AutoLever/commit/b38b842350029262e7a4a7582815164e0e5b5ee5))
* **firmware:** keep a jam or sensor fault latched under a supply fault ([#125](https://github.com/OpenReloading/AutoLever/issues/125)) ([3dde3d4](https://github.com/OpenReloading/AutoLever/commit/3dde3d4fd6fef9d77ca9ce0c6b2e6ac7057d8169))
* **firmware:** refuse settings posts from other sites ([#93](https://github.com/OpenReloading/AutoLever/issues/93)) ([7a74128](https://github.com/OpenReloading/AutoLever/commit/7a741282b684eb87766dc8843b98e0a4e97c1639))
* **firmware:** refuse Wi-Fi passwords of the wrong length ([#138](https://github.com/OpenReloading/AutoLever/issues/138)) ([a15e281](https://github.com/OpenReloading/AutoLever/commit/a15e281148d432b96824db8055bb8819c8c9a7a3))
* **firmware:** reject a bad jam time and keep the Wi-Fi password ([#126](https://github.com/OpenReloading/AutoLever/issues/126)) ([a9a0cf7](https://github.com/OpenReloading/AutoLever/commit/a9a0cf7f1304d46e8902a15a04b61de9c4c6cd91))
* **firmware:** serve the web page in its own task ([#144](https://github.com/OpenReloading/AutoLever/issues/144)) ([68862a9](https://github.com/OpenReloading/AutoLever/commit/68862a9d0a9d45d5fae3916093e2a953303aec02))
* **firmware:** show STOPPING on the display after a stop request ([#92](https://github.com/OpenReloading/AutoLever/issues/92)) ([3d2332e](https://github.com/OpenReloading/AutoLever/commit/3d2332ee814c1e4342d646f15b4a0e2dfc749e66))
* **firmware:** write the relays before the web server runs ([#124](https://github.com/OpenReloading/AutoLever/issues/124)) ([36b0903](https://github.com/OpenReloading/AutoLever/commit/36b09032933af3ad94ea8ec2a66fabba3749a976))

## [0.2.0](https://github.com/OpenReloading/AutoLever/compare/v0.1.0...v0.2.0) (2026-10-28)


### Features

* build guide from the BuildGuide MkDocs plugin ([#5](https://github.com/OpenReloading/AutoLever/issues/5)) ([f6a5ff5](https://github.com/OpenReloading/AutoLever/commit/f6a5ff5188ed6370a1de39b893eb1512e613b7b1)), closes [#4](https://github.com/OpenReloading/AutoLever/issues/4)
* **cad:** DIN rail on heat-set inserts, optional wood-screw holes ([#60](https://github.com/OpenReloading/AutoLever/issues/60)) ([8f9b231](https://github.com/OpenReloading/AutoLever/commit/8f9b231be4da9f885b915e8fb6cdb67555e523cd))
* **cad:** StamPLC control box with the whole unit front in a lid window ([#84](https://github.com/OpenReloading/AutoLever/issues/84)) ([7e9270b](https://github.com/OpenReloading/AutoLever/commit/7e9270b6b6dff668546d8f024c3d636f711d848e)), closes [#72](https://github.com/OpenReloading/AutoLever/issues/72)
* **docs:** header title, footer links, previous and next, 404 ([#54](https://github.com/OpenReloading/AutoLever/issues/54)) ([b79f7e0](https://github.com/OpenReloading/AutoLever/commit/b79f7e0c596b7e8340b149073e80417bd79b4e6d))
* **docs:** social card and self-hosted search ([#57](https://github.com/OpenReloading/AutoLever/issues/57)) ([8e55574](https://github.com/OpenReloading/AutoLever/commit/8e55574ae79d0e4939080231f1fa7cac3d8a917b))
* **firmware:** StamPLC press logic with native test and hardware main ([#83](https://github.com/OpenReloading/AutoLever/issues/83)) ([97ea7f1](https://github.com/OpenReloading/AutoLever/commit/97ea7f1fa74b4276d46337512d1a3e880ac9e034)), closes [#72](https://github.com/OpenReloading/AutoLever/issues/72)
* **firmware:** Wi-Fi access point and home network, status page, settings, OTA ([#85](https://github.com/OpenReloading/AutoLever/issues/85)) ([a63b3e6](https://github.com/OpenReloading/AutoLever/commit/a63b3e692e0c1c1b386364dab4280cb10bed6d67)), closes [#72](https://github.com/OpenReloading/AutoLever/issues/72)
* show tube texts and checks in the tubing guide ([#24](https://github.com/OpenReloading/AutoLever/issues/24)) ([100dfec](https://github.com/OpenReloading/AutoLever/commit/100dfecc142233647324533bccbbc22904f2a4ef))
* **wiring:** plain words, red and black wires, twin ferrules in one step ([#73](https://github.com/OpenReloading/AutoLever/issues/73)) ([468819e](https://github.com/OpenReloading/AutoLever/commit/468819e7e448a5ca86cad25b27fcea41163da69b))


### Bug Fixes

* **cad:** guard adapter pivot eye overlap, space print_plate by real X extent ([#62](https://github.com/OpenReloading/AutoLever/issues/62)) ([bb5bc5b](https://github.com/OpenReloading/AutoLever/commit/bb5bc5b27e4a1231c98a1859feee1e38c68d0832))
* resolve open SonarCloud findings ([#32](https://github.com/OpenReloading/AutoLever/issues/32)) ([b2fa9e7](https://github.com/OpenReloading/AutoLever/commit/b2fa9e7ce7a731dbb0c33708a4de4c12f4fa37cc))
