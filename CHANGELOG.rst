Changelog
=========

2.1.0
-----

- Metadata fixups, tw2.core#90 `382a27e60 <https://github.com/toscawidgets/tw2.sqla/commit/382a27e607be5e4812b6e025b36ed465ededae10>`_
- Add missing require for the tests `2af2469a4 <https://github.com/toscawidgets/tw2.sqla/commit/2af2469a481c478aea3625f44edeccf63edbfde6>`_
- Fix tw.Param: the attribute is always defined and required. `517406037 <https://github.com/toscawidgets/tw2.sqla/commit/5174060376cb144ddcd6b705e42fbcba9ad6d11b>`_
- s/setup/setUp/g `515586419 <https://github.com/toscawidgets/tw2.sqla/commit/515586419d0190963b54983671709ce3c2957b96>`_
- Fix tests `78c544376 <https://github.com/toscawidgets/tw2.sqla/commit/78c544376951f422134c26af100b36d2d0de81ea>`_
- For genshi we should not call __call__ many times on the same the widget `82a997a50 <https://github.com/toscawidgets/tw2.sqla/commit/82a997a5070246ab0fff4a40cf0de88feeed215c>`_
- Some refactoring `f4b7caccb <https://github.com/toscawidgets/tw2.sqla/commit/f4b7caccb11f49f36c1b4926f7ddaff404429320>`_
- Display the onetoone field in a label when we view the data. In this way the HTML table is not too big according to the DB. `e97c34285 <https://github.com/toscawidgets/tw2.sqla/commit/e97c342851d77033bdc0c985f7e6202991ed2371>`_
- Use first the widget defined in the hint `168811e9b <https://github.com/toscawidgets/tw2.sqla/commit/168811e9b8724225e16198bdbaca735295162a6c>`_
- Do not instantiate many times the widget in order to not have a validator defined by the __post_define__. `cbc36dbc4 <https://github.com/toscawidgets/tw2.sqla/commit/cbc36dbc485a861e0624de13e0c007c12d3d2658>`_
- Do not force a validator if it is already defined. Now we can pass a validator in the hint without overwriting it! `480870d22 <https://github.com/toscawidgets/tw2.sqla/commit/480870d222f54bd9403a688f5007a4100880e41d>`_
- Sometimes we don't have any validator `81d953ec9 <https://github.com/toscawidgets/tw2.sqla/commit/81d953ec9d4d333963de23d738ffd80a93a77d6b>`_
- Require the latest sieve. `89d0b44ce <https://github.com/toscawidgets/tw2.sqla/commit/89d0b44cedc8d1998f559a746203fe0ca0d91d6d>`_
- Fix typo `b60d53541 <https://github.com/toscawidgets/tw2.sqla/commit/b60d53541d2b6cfbe70f98335d9e5b351db3b132>`_
- Merge pull request #15 from LeResKP/develop `90d8d15c3 <https://github.com/toscawidgets/tw2.sqla/commit/90d8d15c3c87bff826164ee88642c4960286ffea>`_
- Hack to make sure the tests in tw2test.WidgetTest are called. `3933cd242 <https://github.com/toscawidgets/tw2.sqla/commit/3933cd2425058b5b27dc8326c6a8f6ea65da4d9d>`_
- label_field template need escape param defined `5e92a00c9 <https://github.com/toscawidgets/tw2.sqla/commit/5e92a00c98477b2f4753f485a70ce36b016bffed>`_
- Merge pull request #16 from LeResKP/develop `e2c49b77e <https://github.com/toscawidgets/tw2.sqla/commit/e2c49b77e525e916de986f8fb4fca3fb97161289>`_
- Fix test `a3f270cd6 <https://github.com/toscawidgets/tw2.sqla/commit/a3f270cd6d6191743c7d7529a0c1eadc1f8547c7>`_
- Also get first the hint for the relation fields. `9c60f4e66 <https://github.com/toscawidgets/tw2.sqla/commit/9c60f4e66c4721e2bdee3fccec0f93b07ad4ec27>`_
- Add FactoryWidget which is used to pass parameters to the widget choosed by the factory `cebe3c75d <https://github.com/toscawidgets/tw2.sqla/commit/cebe3c75d790bf1c78ae2d169f1147e1b8f35053>`_
- Be able to display HTML in the view if get_tws_view_text function is defined on the object. We don't want to poluate __unicode__ with some HTML. `e8bbe8fae <https://github.com/toscawidgets/tw2.sqla/commit/e8bbe8faef706d746f42d5eb6981bc2bbc549f10>`_
- Sort all the relation properties `b3f31e29b <https://github.com/toscawidgets/tw2.sqla/commit/b3f31e29be09707fcfcfcaea4ef4002dbf2f3f86>`_
- Merge pull request #17 from LeResKP/develop `fbdb8337f <https://github.com/toscawidgets/tw2.sqla/commit/fbdb8337fc1d77be8ab36940758fa8046952c175>`_

2.0.6
-----

- Add forgotten doc `4d44d1f54 <https://github.com/toscawidgets/tw2.sqla/commit/4d44d1f5435405d02ad6b83f2060ed2ef8f45a00>`_
- On the non required onetoone relations, we only validate the required children if at least one value is posted. `bae333c44 <https://github.com/toscawidgets/tw2.sqla/commit/bae333c44f7e95bdf294c2a3041ace8c580174fa>`_
- * Delete the old value from the DB for the onetoone field * Improve the tests `8d75aa8f2 <https://github.com/toscawidgets/tw2.sqla/commit/8d75aa8f27e6d9dc079d21fd6604b4988e00a2ab>`_
- If no value posted for onetoone field, we return None to delete the value from the DB `538e48eb9 <https://github.com/toscawidgets/tw2.sqla/commit/538e48eb94584cd97961a12b1104e252ef7fd418>`_
- Test the non required onetoone field `35430e7d1 <https://github.com/toscawidgets/tw2.sqla/commit/35430e7d15a38fb1b5498ceaf4ccd9522d308926>`_
- Merge pull request #12 from LeResKP/feature/onetoone_relation `aab98fa59 <https://github.com/toscawidgets/tw2.sqla/commit/aab98fa59e39f83b46f86539ed9236ea908f9ab8>`_
- 2.0.5 `704e5a38b <https://github.com/toscawidgets/tw2.sqla/commit/704e5a38b13fa00a3d062927b78f5ddf17eb0815>`_
- 2.0.5 `e62b6f975 <https://github.com/toscawidgets/tw2.sqla/commit/e62b6f97512e76406ea512b738d38f0f8d14867c>`_
- Some progress on modernizing tests. `c19f41fd2 <https://github.com/toscawidgets/tw2.sqla/commit/c19f41fd2c6bfa691f3c7ff757e2d7d5f3ccc5bc>`_
- Failures done.  Errors left. `7a58fb7ca <https://github.com/toscawidgets/tw2.sqla/commit/7a58fb7ca28931a8cf620466808550a05b29e807>`_
- Last errors dealt with.  Thank god. `3a75628d8 <https://github.com/toscawidgets/tw2.sqla/commit/3a75628d80a2cd2aac663756a80478e6396dd8c9>`_
