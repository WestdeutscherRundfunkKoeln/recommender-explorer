# Recommender Explorer

Recommender Explorer is a GUI based tool for evaluating and testing content-2-content and user-2-content recommendations. Users can select the start-content by various means (date-range, url, user-cluster, id) and manipulate the generated recommendations with filter and ranking widgets. It's also possible to compare the results of different models and algorithms side-by-side. In addition, Recommender Explorer contains a number of microservices, which can be used to ingest and embed items into an OpenSearch index.

The primary purpose of Recommender Explorer is to provide  a means for interacting with your own, custom recommendation algorithms outside their actual production environment. 

## Infos for developers

Recommender Explorer is a python application based on Panel.

Key architectural components of the application are:

+ Python
+ [Panel](https://panel.holoviz.org/)
+ [OpenSearch]([https://aws.amazon.com/de/what-is/opensearch/])

It roughly follows the [MVC pattern](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller)

### Set up Opensearch connectivity

Recommender Explorer uses OpenSearch for metadata and vector storage. In order to a run a development instance of Recommender Explorer, you have to expose two variables to your environment:

```
OPENSEARCH_PASS=******
OPENSEARCH_HOST=******
```
in order to gain access to your OpenSearch instance. 

### Set up AWS connectivity

Recommender Explorer requires AWS connectivity for models hosted in Sagemaker. Follow the instructions [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html) in order to set up AWS connectivity for your development environment.

### Set up Recommender Explorer

#### Checkout the sources
```git clone git@github.com:WestdeutscherRundfunkKoeln/recommender-explorer.git <local_path>```

#### Create a virtual environment and install dependencies

```
python3 -m venv ~/my_envs/reco-xplorer
source ~/my_envs/reco-xplorer/bin/activate
pip3 install -r requirements.txt
```

#### Adapt the configuration file
Copy the file <local_path>/config/config_template.yaml to </path/to/your_config_file.yaml> and configure your model endpoints and mappings accordingly. 
```scripts/validate.py --config </path/to/your_config_file.yaml>```

### Start Recommender Explorer in development mode
```scripts/run.sh -c </path/to/your_config_file.yaml>```

### Run tests
```pytest --config=</path/to/your_config_file.yaml>```

### Build deployable Docker image
```docker build --no-cache -t reco_explorer:0.1 . ```

### Run Docker image
```docker run --env OPENSEARCH_PASS="<YOUR_OPENSEARCH_PW>" --env AWS_ACCESS_KEY_ID="<YOUR_AWS_KEY_ID>" --env AWS_SECRET_ACCESS_KEY="<YOUR_AWS_SECRET>" --env AWS_DEFAULT_REGION="eu-central-1"   --rm -it -p 8080:80 --name recoxplorer reco_explorer:0.1```

### Run microservices locally
To run the backend services and opensearch locally just execute:
```docker-compose up```
If you have a specific mapping definition you might need to change the corresponding environment variable in the docker-compose.yaml.

### Run linter/formatter
- Install the pre-commit package using pip: ```pip install pre-commit```
- Set up pre-commit to run the linter/formatter automatically before each commit: ```pre-commit install``` 
- To run the formatter on all files, execute ```pre-commit run --all-files```
- To run the formatter on specific files, execute ```pre-commit run --files <FILENAME>```

## How to contribute

Recommender Explorer as a whole is distributed under the MIT license. You are welcome to contribute code in order to fix bugs or to implement new features. 

There are three important things to know:

1. You must be aware and agree to a Contributors License Agreement (CLA) before you can contribute. However, if your contribution constitutes as a small code contribution, you do not need a CLA. Our CLAs are largely derived from the ones used by Apache Software Foundation (https://www.apache.org/licenses/contributor-agreements.html)
2. There are several requirements regarding code style, quality, and product standards which need to be met (we also have to follow them). 
3. Not all proposed contributions can be accepted. Some features may e.g. just fit a third-party add-on better. The code must fit the overall direction of Recommender Explorer and really improve it. The more effort you invest, the better you should clarify in advance whether the contribution fits: the best way would be to just open an issue to discuss the feature you plan to implement (make it clear you intend to contribute).

### Process of a contribution

- Make sure the change would be welcome (e.g. a bugfix or a useful feature); best do so by proposing it in a GitHub issue on our repository. Also check for similar issues that might already be present. 
- Create a branch forking the Recommender Explorer repository and do your change
- Commit and push your changes on that branch
- In the commit message, describe the problem you fix with this change.
- Describe the effect that this change has from a user's point of view.
- Describe the technical details of what you changed. It is important to describe the change in a most understandable way so the reviewer is able to verify that the code is behaving as you intend it to.
- If your change fixes an issue reported at GitHub, add the following line to the commit message:
Fixes #(issueNumber)
- Create a Pull Request
- Wait for our code review and approval, possibly enhancing your change on request
- Once the change has been approved we will inform you in a comment
- We will close the pull request, feel free to delete the now obsolete branch


# RecoExplorer UI Configuration

This Documentation will provide insights in the possibilities of creating your own Nav Bar UI in the Python panel application: RecoExplorer. You can define what widgets will be shown and how they can be configured to be filters or search options for the users. The config itself is a yaml file which needs to be defined in the application, with a given structure and rules.

## File Contents
You can define different widgets in the configuration and some of these can also again hold different widgets which can be defined by you. These are your options:

## General UI Configuration
To Configure A UI, the config file needs to contain some Key Value Pairs. In these some general Defaults will be set and the blocks are configured, which contain the widgets themselves.

### Config Overview
| keyword           | mandatory | fallback value       | description                                                                                                     |
|-------------------|-----------|----------------------|-----------------------------------------------------------------------------------------------------------------|
| title             | no        | Recommender Explorer | Title of the App. Is Shown in the visible Header                                                                |
| logo              | no        | -                    | Can contain a URL to an Icon or Logo Image. If empty, no Logo will be displayed in Header                       |
| header_background | no        | #194569              | Sets the Color of the visible Header Band which also contains the Title and the Logo                            |
| page_size         | no        | 4                    | Sets the Page Size of the result row, so 4 means, you can see 4 recommandations for a start item initially      |
| blocks            | yes       | -                    | A list of Blocks, which contain the Widgets Configuration. At least on block must be configured to show some UI |
| custom_css        | no        | -                    | If you want to style UI Elements you can change appearance by adding custom css to the application              |


### Example of a UI Configuration

	ui_config:
	  title: A Test Example
      logo: https://www.urlToALogo.com/logo.svg
      header_background: #194569
      page_size: 5
      blocks:
	    - label: 'Block A'
          components:
            ...
      custom_css:
        '""
        #header .app-header .title {
            padding-left: 0;
        }
        ""'
This configuration will create a Header with a Title, Logo and a Background Color and also a NavBar with one Block ('Block A'). This Block can contain all the widgets configuration described in this Documentation.

## Block
All widgets are organized in Blocks. Every Widgets need to be in an Block to be shown and so you need at least one block in your navigation. 

### Block Config Overview
| keyword           | mandatory | fallback value         | description                                                                                                                                                                                                                                                                                                                                              |
|-------------------|-----------|------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| label             | no        | Default Block Headline | headline of the block                                                                                                                                                                                                                                                                                                                                    |
| show_reset_button | no        | True                   | Switch if a reaset button for the block should be displayed or not                                                                                                                                                                                                                                                                                       |
| components        | yes       | -                      | contains the configuration of the widgets which can be shown. Can be all of the widgets named in this Documentation                                                                                                                                                                                                                                      |
| linkto            | no        | -                      | links the block to the required accordion that's a part of the Accordion of Cards Widget that must has the ui_acc activated. The value is numeric and starts with 0 which points to the first accordion and so on. not giving a value here simply keeps the block always in the UI so it doesn't get affected by the changes "selection" of an accordion |
### Example of a Block Configuration

	- label: 'Block A'
      linkto: "0"
	  components: 
	    - type: 'accordion'
          ...
        - type: 'text_field'
          ...
    - label: 'Block B'
      linkto: "1"
      show_reset_button: False
      components:
        - type: 'multi_select'
          ...
        - type: 'accordion'
          ...
        - type: 'date_time_picker'
          ...


### Example with Accordion with Cards Widget that controls the UI

    - label: Modelle wählen
          components:
            - type: accordion_with_cards
              ui_acc: true
              content:
                - type: accordion
                  label: A
                  content:

                - type: accordion
                  label: B
                  content:

        - label: 'Block A'
              linkto: "0" #this block will be shown on the UI when the accordion with lable A is selected
              components: 
                - type: 'accordion'
                  ...
                - type: 'text_field'
                  ...
            - label: 'Block B'
              linkto: "1"  #this block will be shown on the UI when the accordion with lable B is selected
              show_reset_button: False
              components:
                - type: 'multi_select'
                  ...
                - type: 'accordion'
                  ...
                - type: 'date_time_picker'
                  ...

      
            

This Configuration will create 2 Blocks with Headlines 'Block A' and 'Block B'. Block A will contain a Accordion Widget and a Text Field Widget and Block B will contain a Multi Select Widget, a Accordion Widget and a DateTimePicker Widget. Also it will not display a reset button. Be aware that these Widgets need configuration in itself. See each Widgets Documentation here.

## Text Input Widget

### Text Input Config Overview
| keyword            | mandatory | fallback value | description                                                                                                                                                                                                                            |
|--------------------|-----------|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| type               | yes       | -              | widget type definition: **text_field**                                                                                                                                                                                                 |
| label              | no        | -              | at least one **must** be set: label or placeholder                                                                                                                                                                                     |
| placeholder        | no        | -              | at least one **must** be set: label or placeholder                                                                                                                                                                                     |
| validator_function | yes       | -              | a validator function name, which checks the given content (here a date) in the controller before searching. **Validator function must be defined in reco_controller.py**                                                               |
| accessor_function  | yes       | -              | a accessor function name, which is used to create the search query. **Accessor function must be defined in base_data_accessor_opensearch.py**                                                                                          |
| url_parameter      | no        | -              | text inputs can be set by a url parameter. This parameter name can be set here, so when its named: aParameterName a call like .../RecoExplorer?aParameterName=test would set test into the text field an trigger a search immediately. |
| component_group      | no        | -              | defines the component_group of the widget gets registered to. |
| tooltip      | no        | !! Hinterlegen Sie bitte einen beschreibenden Text zu diesem Parameter in der UI-Configuration.!! | tooltip to show to the user |

### Example of a Text Input Widget Configuration

	type: 'text_field'
	label: 'A Test Text Field'
	placeholder: 'A test placeholder'
	validator_function: '_check_text_field_content'
	accessor_function: 'get_item_by_text_field_content'
	url_parameter: 'aParameterName'

This config would create a Text Field Widget with a label and a placeholder. Its content will be validated by the _check_text_field_content function in the controller and an item would be searched by the get_item_by_text_field_content function in the controller. Also a url call like ...?aParameterName=abc would insert abc into the text field on load and directly trigger a search (and validation)

## Date Time Picker

### Date Time Picker Config Overview

| keyword           | mandatory | fallback value                 | description                                                                                                                                                              |
|-------------------|-----------|--------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| type              | yes       | -                              | widget type definition: **date_time_picker**                                                                                                                             |
| name              | no        | Default Date Time Picker Label | headline of the date time picker widget                                                                                                                                  |
| label             | no        | -                              | label which gets set in the widgets params (can be **important** for date search)                                                                                        |
| validator         | yes       | -                              | a validator function name, which checks the given content (here a date) in the controller before searching. **Validator function must be defined in reco_controller.py** |
| accessor_function | yes       | -                              | a accessor function name, which is used to create the search query. **Accessor function must be defined in base_data_accessor_opensearch.py**                            |

### Example of a Date Time Picker Widget Configuration

    type: 'date_time_picker'
	name: 'A Test Date Picker'
	label: 'startdateinput'
	validator: '_check_date'
	accessor_function: 'get_items_by_date'

### A real live use

If you want to have a date search for the start items (I want to see start items from day and time x to day and time y) you can use a configuration like this to archive this in the current code base:

    -   type: 'date_time_picker'
        name: 'Startdatum'
        label: 'startdateinput'
        validator: '_check_date'
        accessor_function: 'get_items_by_date'
    -   type: 'date_time_picker'
        name: 'Enddatum'
        label: 'enddateinput'
        validator: '_check_date'
        accessor_function: 'get_items_by_date'

## Date Time Quick Select

### Date Time Quick Select Config Overview

| keyword           | mandatory | fallback value   | description                                          |
|-------------------|-----------|------------------|------------------------------------------------------|
| type              | yes       | -                | widget type definition: **date_time_quick_select**   |
| label             | no        | Today            | label shown on the quick select button               |
| start_picker_label| no        | start            | label of the start datetime picker widget            | 
| end_picker_label  | no        | end              | label of the end datetime picker widget              | 
| start_delta_days  | no        | 0                | how many days in the past the start date is          |
| end_delta_days    | no        | 0                | how many days in the past the end date is            |

### Example of a Date Time Quick Select Widget Configuration

    type: date_time_quick_select
    label: last week
    start_picker_label: startdateinput
    end_picker_label: enddateinput
    start_delta_days: 6
    end_delta_days: 0

### A real live use

If you want to have a quick selection right after the date search simply put: 

    -   type: 'date_time_picker'
        name: 'Startdatum'
        label: 'startdateinput'
        validator: '_check_date'
        accessor_function: 'get_items_by_date'
    -   type: 'date_time_picker'
        name: 'Enddatum'
        label: 'enddateinput'
        validator: '_check_date'
        accessor_function: 'get_items_by_date'
    -   type: date_time_quick_select
        label: last week
        start_picker_label: startdateinput
        end_picker_label: enddateinput
        start_delta_days: 6
        end_delta_days: 0


## Multi Select Widget

### Multi Select Config Overview

| keyword                   | mandatory | fallback value | description                                                                                                                                                                                                                                                                                                              |
|---------------------------|-----------|----------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| type                      | yes       | -              | widget type definition: **multi_select**                                                                                                                                                                                                                                                                                 |
| label                     | no        | -              | headline of the multi select widget                                                                                                                                                                                                                                                                                      |
| register_as               | no        | -              | sets the value which gets registered at the (search) controller. Filters get defined by that value. See ['Multi Select Widget as a Filter'](#multi-select-filter-headline-link) in this Documentation to what options you have and what these filters do.                                                                |
| linked_filter_name        | no        | -              | only needed for upper item filter widget. For details see See ['Multi Select Widget as a Filter'](#multi-select-filter-headline-link) in this Documentation                                                                                                                                                              |
| filter_category: 'genres' | no        | -              | only needed for upper item filter widget. For details see See ['Multi Select Widget as a Filter'](#multi-select-filter-headline-link) in this Documentation                                                                                                                                                              |
| options                   | no        | -              | define options which should be displayed in the multi select widgets. For details see See ['Multi Select Options'](#multi-select-options-headline-link) in this Documentation. **At least one** options key must be defined for a multi select widget (either **options**, **dictionary_options** or **option_default**) |
| dictionary_options        | no        | -              | define options which should be displayed in the multi select widgets. For details see See ['Multi Select Options'](#multi-select-options-headline-link) in this Documentation. **At least one** options key must be defined for a multi select widget (either **options**, **dictionary_options** or **option_default**) |
| option_default            | no        | -              | define options which should be displayed in the multi select widgets. For details see See ['Multi Select Options'](#multi-select-options-headline-link) in this Documentation. **At least one** options key must be defined for a multi select widget (either **options**, **dictionary_options** or **option_default**) |
| tooltip      | no        | !! Hinterlegen Sie bitte einen beschreibenden Text zu diesem Parameter in der UI-Configuration.!! | tooltip to show to the user |


### Example of a Multi Select Widget Configuration

	type: 'multi_select'
	label: 'A Test Multi Select'
	register_as: 'filter'
	options:
		display_name: 'Option A'
		display_name: 'Option B'
		...

This configuration would create a Multi Select Widget which is registered as a filter at the controller (see ['Multi Select Widget as a Filter'](#multi-select-filter-headline-link) in this Documentation for details). It has a label and two Basic Options ('Option A' and 'Option B') See ['Multi Select Options'](#multi-select-options-headline-link) in this documentation for details.

### <a id="multi-select-options-headline-link"></a>Multi Select Options

There are multiple kinds of option definitions you can configure. Multi Select Options are in the end always a list of labels with different params and different kind of params are need, for example if you want to put some filter in a multi select. The different types are:

#### Basic Options

- When in a multi select config the key is named: **options**, it means that basic options are defined.
- Basic Options only have a label and an optional default value in which you can select the default selected option
- A basic option config with three options and the second one is selected when the application is started would look like this:

       options:  
          -   display_name: 'Option A'  
          -   display_name: 'Option B'  
              default: True  
          -   display_name: 'Option C' 

#### Dictionary Options

- When in a multi select config the key is named: **dictionary_options**, it means that basic options are defined.
- Dictionary Options have a key value pair where the key is the options label and the value is the option value (used for example when you want to create a filter)
- A dictionary option config with three options would look like this:

      dictionary_options:  
          -   Option A: 'categories_a'  
          -   Option B: 'categories_b'  
          -   Option C: 'categories_c' 

#### Default Options

- When in a multi select config the key is named: **option_default**, it means that default options are defined.
- Default Options are not defined in the config. Instead, the config passes a key to the controller which loads all options from the search server. This key has to be defined before, so that this method can work.
- A default option config with x options could look like this:

      option_default: 'categoriesAtoC'


### <a id="multi-select-filter-headline-link"></a>Multi Select Widget as a Filter

You can configure filters for search results and recommendations as a Multi Select Widget in the configuration File. To do this, you can select a **register_as** value on a mutli select widget configuration. There are 4 types of filters, you can choose one of them:

#### Model Choice
When you register a model choice multi select it contains information to the different models a user can select to search for recommendations and compare them between the models. There are no other conditions for this kind of filter, except, that the models have do be defined in the configuration filte (c2c_config -> c2c_models) and the display_name from the model choice multi select must be the same as the display name in the models config. The **register_as** in configuration must be set to: **model_choice**

##### Example for a Model Choice Filter Configuration

If your model configration looks like this:

    c2c_config:  
	    c2c_models:  
	        Model-A:  
	            display_name: 'Model-A'
	            handler: 'handler_name'
	            endpoint: 'handler_endpoint'
	            start_color: ...
	            reco_color: ...
	            content_type: 'item_dto'
	            deafult: True  
	        Model-B:  
	            display_name: 'Model-B'
	            handler: 'handler_name'
	            endpoint: 'handler_endpoint'
	            start_color: ...
	            reco_color: ...
	            content_type: 'item_dto'
	            deafult: False  
	        Model-C:  
	            display_name: 'Model C'
	            handler: 'handler_name'
	            endpoint: 'handler_endpoint'
	            start_color: ...
	            reco_color: ...
	            content_type: 'item_dto'
	            default: False  

A multi select widget configuration which is used to select a model for the recommendations would look like this:

	   type: 'multi_select'
	   label: 'c2c_config'
	   register_as: 'model_choice'
	   options:
		   -    display_name: 'Model-A'
		        default: True
		   -    display_name: 'Model-B'
		   -    display_name: 'Model-C'

When the multi select is registered as model_choice, you can use basic options (see multi select options in this documentation) to list your available models (matching works with the display_name). Optional is a default value. This means, you can choose the model which is selected in the start when the application is loaded.

#### Upper Item Filter

With an upper item filter you can filter the item filters and start item results. When an upper item filter gets set, it changes the start results but also another item filter. The **register_as** in configuration must be set to: **upper_item_filter**

##### Example for an Upper Item Filter Configuration

For an Item Filter you can define a upper item filter. If your Item Filter Multi Select Widget is configured like this

    type: 'multi_select'
    label: 'item_filter_A' 
    register_as: 'item_filter'
    options:
	    ...

You can configure an Upper Item Filter Multi Select Widget which references the item filter by name (**linked_filter_name**). The options of an Upper Item Filter Widget are configured as  dictionary options (see multi select options in this documentation)

    type: 'multi_select'
    label: 'test_upper_item_widget'
    register_as: 'upper_item_filter'
    linked_filter_name: 'item_filter_A' ## In this application the categories are "genres" and "subgenres"
    filter_category: 'a_category'
    dictionary_options:
	    Option A: 'categories_a'
	    Option B: 'categories_b'
	    Option C: 'categories_c'

#### Item Filter

With an upper item filter you can filter the start item results. When an item filter gets set, it changes the start results by using the selected filter. The Filter gets set when a user selects it in the Filter Multi Select Widget. The **register_as** in configuration must be set to: **item_filter**

##### Example for an Item Filter Configuration

An Item Filter Multi Select Widget is configured like this. The Options of an Item Filter Widget are configured as default options (see multi select options in this documentation)

    type: 'multi_select'
    label: 'item_filter_A' 
    register_as: 'item_filter'
    option_default: 'categoriesAtoC'

#### Recommendation Filter

With an recommendation filter you can filter the recommended items based on the start item results. When an recommendation filter gets set, it changes the recommended results by using the selected filter. The Filter gets set when a user selects it in the Recommendation Multi Select Widget. The **register_as** in configuration must be set to: **reco_filter**

##### Example for a  Recommendation Filter Configuration

A Recommendation Filter Multi Select Widget is configured like this. The Options of a Recommendation Filter Widget are configured as dictionary options (see multi select options in this documentation)

    type: 'multi_select'
    name: 'Recommendation Test Filter'
    label: 'reco-test-filter'
    register_as: 'reco_filter'
    dictionary_options:
	    Option A: ['filterA', 'id']
	    Option B: ['filterB', 'description']
	    Option C: ['filterC', 'url']

A Recommendation Filter Multi Select Widget can also be configured with action options. You can have multiple action options for one multi select widget. An action option is configured as a key value pair where the key is the multi select option and the value is the label of the target Widget. When configured correctly, the target Widget will be hidden on load and gets visible when configured option is selected. All of these Widgets must be in a single Accordion.

    type: 'multi_select'
    name: 'Recommendation Test Filter'
    label: 'reco-test-filter'
    register_as: 'reco_filter'
    dictionary_options:
	    Option A: 'filterA'
	    Option B: 'filterB'
	    Option C: 'filterC'
    action_option:
        filterC: 'trigger_widget_label'

    type: 'multi_select'
    name: 'Trigger_Widget'
    label: 'trigger_widget_label'
    register_as: 'reco_filter'
    dictionary_options:
	    Option D: 'filterD'
	    Option E: 'filterE'
	    Option F: 'filterF'

In this example the second multi select Widget is hidden on load. When the User Clicks the Option C in the first multi select Widget, the second one gets visible. This second Widget can be anything and used without restrictions.

## Accordion Widget

###  Accordion Config Overview

| keyword | mandatory | fallback value             | description                                                                                                                                                                                                                                                                            |
|---------|-----------|----------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| type    | yes       | -                          | widget type definition: **accordion**                                                                                                                                                                                                                                                  |
| label   | no        | Default Accordion Headline | headline of the accordion widget                                                                                                                                                                                                                                                       |
| active  | no        | []                         | When there are multiple widgets in the accordion this defines which accordion content widget should be open when the application is started (0 -> first). Each widget which should be open must be in the list, when the list is empty (fallback) no accordion content widget is open. |
| content | yes       | -                          | This defines the content of the accordion. There can be multiple entries of other widgets here which need to be exactly configured like they would, when standing alone. Available widget options are: TextWidget, MultiSelectWidget, DateTimePickerWidget, RadioBoxWidget             |

### Example of a Accordion Widget Configuration

    -	type: 'accordion'
	    label: 'A Test Accordion'
	    active: 0
	    toggle: False
	    content:
		    -	type: 'multi_select'
			    ...
		    -	type: 'text_field'
			    ...
This configuration would create a Accordion Widget with a label and two contents inside, a Multi Select Widget and a Text Field Widget. The Multi Select Widget will be initially visible and wont close when the text field is selected.  Be aware that the widgets inside the content are treated as standard widgets so they have all the features and requirements as if you would confige it outside the Accordion.

## Accordion Cards Widget

###  Accordion Cards Config Overview

| keyword | mandatory | fallback value | description                                                                                                                                                                                                                                                                                     |
|---------|-----------|----------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| type    | yes       | -              | widget type definition: **accordion_with_cards**                                                                                                                                                                                                                                                |
| active  | no        | [0]            | When there are multiple widgets in the accordion this defines which accordion content widget should be open when the application is started (0 -> first). Each widget which should be open must be in the list, when the list is empty (fallback) the first accordion content widget is open.   |
| toggle  | no        | False          | Option Flag which defines if more than one accordion content type can be opened if there are multiple ones. If True and first accordion content is opened and user opens the second accordion content, the first one gets closed automatically.                                                 |
| content | yes       | -              | This defines the cards of the accordion. There can be multiple entries of other accordion widgets here which need to be exactly configured like they would, when standing alone.                                                                                                                |
| ui_acc  | no        | -                          | Tells if this widget can control the UI and will have specific widgets linked to it and therefore we will monitor its changes                                                                                                                                                       |
### Example of an Accordion Cards Widget Configuration

    -   type: 'accordion_with_cards'
	    active: 0
	    toggle: True
	    content:
		    -	type: 'accordion'
			    ...
		    -	type: 'accordion'
			    ...
This Widget Configuration is just a Pool if you want to create multiple accordion widgets which can interact with each other (Toggle). So you can just use this if you want to display multiple accordion cards

## Radio Box Widget

### Radio Box Config Overview

| keyword | mandatory | fallback value | description                                                                                                                                                                                                                                                                             |
|---------|-----------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| type    | yes       | -              | widget type definition: **radio_box**                                                                                                                                                                                                                                                   |
| label   | no        | -              | headline of the radio widget                                                                                                                                                                                                                                                            |
| options | yes       | -              | a list of options of the Radio Box. Each Option gets its  own radio Button with a Label and only gets visible when selected. Otherwise its hidden. The default option is the first one (its selected and visible). Options have a Label and are other widget configuration. See example |

### Example of a Radio Box Widget Configuration

    type: 'radio_box'
	label: 'A Test Radio Box'
	options:
		Option A:
			type: 'text_field'
			...
		Option B:
			type: 'multi_select'
			...
		Option C:
			type: 'date_time_picker'
			...

This Example would create three radio Buttons with the labels: Option A, Option B and Option C. The Radio Button Option A would be selected initially and under the Radio Box, the configured Text Field will be visible. When you select another Radio Button, the Text Field will be hidden and the selected Option Widget will be visible. Be aware that the widgets inside the option are treated as standard widgets so they have all the features and requirements as if you would confige it outside the Radio Box.

## Slider Widget

### Slider Config Overview

| keyword | mandatory | fallback value | description                                                                                                                                                                                                                                                                             |
|---------|-----------|----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| type    | yes       | -              | widget type definition: **slider**                                                                                                                                                                                                                                                   |
| name    | no        | Wert           | headline of the slider widget                                                                                                                                                                                                                                                            |
| start   | no        | 0.0            | start value of the slider                                                                                                                                                                                                                                                            |
| end     | no        | 1.0            | end value of the slider                                                                                                                                                                                                                                                            |
| step    | no        | 0.1            | step value of the slider
| unit    | no        | -              | unit that will be displayed after the slider value
| label   | no        | relativerangefilter_duration | defines the filter that will be applied
| component_group   | no        | reco_filter | defines component_group the filter that will be assigned to
| tooltip      | no        | !! Hinterlegen Sie bitte einen beschreibenden Text zu diesem Parameter in der UI-Configuration.!! | tooltip to show to the user |

### Example of a Slider Widget Configuration

    type: 'slider'
    name: 'Länge'
    start: 0.0
    end: 50.0
    step: 0.5
    unit: 's'
    label: 'relativerangefilter_duration'
    component_group: 'reco_filter'

## Text Area Input Widget

### Text Area Input Config Overview

| keyword            | mandatory | fallback value          | description                                                                                                                                                                                                                                       |
|--------------------|-----------|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| type               | yes       | -                       | widget type definition: **text_area_input**                                                                                                                                                                                                       |
| label              | no        | Default Text Area Input | headline of the text area input widget                                                                                                                                                                                                            |
| placeholder        | no        | -                       | placeholder value in the text area input widget                                                                                                                                                                                                   |
| validator_function | no        | _check_text             | a validator function name, which checks the given content in the controller before searching. **Validator function must be defined in reco_controller.py**                                                                                        |
| accessor_function  | no        | get_item_by_text        | a accessor function name, which is used to create the search query. **Accessor function must be defined in base_data_accessor_opensearch.py**                                                                                                     |
| url_parameter      | no        | -                       | text area inputs can be set by a url parameter. This parameter name can be set here, so when its named: aParameterName a call like .../RecoExplorer?aParameterName=test would set test into the text area input and trigger a search immediately. |


### Example of a Text Area Input Widget Configuration

    type: 'text_area_input'
    label: 'A Text Area Input Widget'
    placeholder: 'Insert text here'
    validator_function: _a_validator_function
    accessor_function: a_accessor_function
    url_parameter: 'test'

This Example would create a Text Area Input Widget. It has a label and a placeholder value. It takes a text wich gets validated by: _a_validator_function and uses: a_accessor_function for the search. When an url parameter named test is given, the value of this parameter is set into the text area input. 


# RecoExplorer Custom Data

This Documentation will provide insights in the possibilities of creating your own RecoExplorer Content Type to make this app work with your Data Structure and 
Mapping of the Meta Data Structure your Search Service will provide or just map your Open Search Response Keys to the default DTO which is already defined.

## Content Item DTO
At first you will have to define and implement a ContentItemDto Class in python in src/dto. This dto should look like this: 

    import constants
    from dataclasses import dataclass
    from dto.item import ItemDto
    
    @dataclass
    class NewContentItemDto(ItemDto):
      id: str = ''
      title: str = ''
      description: str = ''
      duration: int = 0
      imageUrl: str = ''
      _viewer: str = ''

      @property
      def viewer(self) -> str:
        if self._position == constants.ITEM_POSITION_START:
            self._viewer = 'NewContentStartCard@view.cards.new_cards.new_content_start_card'
        elif self._position == constants.ITEM_POSITION_RECO:
            self._viewer = 'NewContentRecoCard@view.cards.new_cards.new_content_reco_card'
        else:
            raise TypeError('Unknown Item position [' + self._position + ']')
        return self._viewer

This dto will be used to store the request from your search service or endpoint into items so that the Reco Explorer can internally work with the items. 
To archive that, you will have to set the new ContentItemDto class in the c2c config file of your Reco Explorer Instance as the content_type:

    c2c_config:
      c2c_models:
          A-New-Model:
              display_name: 'A-New-Model'
              handler: '...'
              endpoint: '...'
              start_color: '...'
              reco_color: '...'
              content_type: 'NewContentItemDto'
              default: True

Now the RecoExplorer will try to map the result of your search request (or endpoint result) to the given ContentItemDTO Class. If the search or endpoint result 
json has a different structure than the Standard OpenS Search Service Response, you will need a custom Item Accessor. For more information about this, see 
section Item Accessor in this documentation.

### Custom Field Mapping
The easiest way for the custom mapping is to name the vars in the DTO Class like the keys of the item you want to map. So in the given example, an Item from the 
response has a key named "id" and a key named "description" and so on. If you want additional mapping here, you can define it in the config. If the Items in 
your response have the same json structure as the ones in the default ContentItemDto class (all in one json level) but just other key names, it would be much 
easier to use a custom field mapping than implement a whole new DTO for your items. A field mapping would look like this:

      field_mapping:
        "created": "availableFrom"
        "id": "externalid"

In this example there would be a key named "availableFrom" in the Item response. There is no "availableFrom" key in the ContentItemDto class (which is used in 
default case) and so you can use the custom mapping to map the value from the custom key to a key name in the item dto class. Here the "availableFrom" Key from 
the response is mapped to the "created" key from the item dto. The Value behind it will be saved in created in the dto. You dont need to map all keys from your 
response to the dto. When the key in the dto and the item response is the same it gets mapped automatically and if its not mapped its default empty in the DTO.

## Custom Result Cards (Frontend)
When a custom new ContentItemDto is implemented that usually also means a new Frontend Configuration is needed. The Result View in Reco Explorer is called a
Card and usually there is a least one Card per DTO because Cards gets the infos from a DTO and present it in the Explorer. What Result Card is displayed in the 
Explorer is defined in the DTO Class itself. The DTO needs a viewer function which returns a String like: 
"NewContentStartCard@view.cards.new_cards.new_content_start_card" That means there need to be a NewContentStartCard Class in 
view/cards/new_cards/new_content_start_card which gets displayed for the result. 

### Card Implementation
For a example how Cards can work its the best to check the "ContentCard" class in /view/cards. Here Values from the DTO (in this case ContentItemDto) get 
mapped to the card and the ContentStartCard() and ContentRecoCard() are implementations of this ContentCard(). The Implementations are the ones which get
actually shown.

## Custom Item Accessor
When you have a custom search result or endpoint response its possible, that the structure of the response does not fit to the ones the Open Search Service 
returns. In that case you need to implement a custom Item Accessor which gets that custom response, gets the items from it and maps every key to the configured 
DTO. The custom Item Accessor needs to be implemented and attached to the model config in the config.yaml like this:

      New-Model:
        display_name: 'New-Model'
        handler: '...'
        item_accessor: 'BaseDataAccessorNewAccessor@model.newService.base_data_accessor_new_accessor'
        ...

This Accessor Class will need all accessor_methods which are defined for the widgets (which get the raw response from your service of choice) and a function
get_ items_from_response() which will take the raw (for example json response) and create item Dtos from the items in the response. You wont have to do more,
When the ContentItemDto and the Resulting Cards are defined correctly, the Reco Explorer should now work with the custom Service (Response)
