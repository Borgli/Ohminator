import React, {useState} from "react";
import Card from "./Card";

const GeneralSettingsCard = ({prefix}) => {
    // TODO Implement setting prefix
    const [prefixTemp, setPrefixTemp] = useState('');

    return (
        <section id="general-settings" className="section">
            <Card title="General settings">
                <div id="prefix" className="field">
                    Prefix
                    <input id="prefix-input" className="input" type="text" placeholder={prefix}/>
                </div>
            </Card>
        </section>
    );
}

export default GeneralSettingsCard;