#include "expression_matcher.h"

ExpressionMatcher::ExpressionMatcher(char const to_match[], size_t const size_in){
    current_match_size = min(size_in, max_to_match_size);

    #if EXPRESSION_MATCHER_DEBUG
        Serial.print(F("D current_match_size: ")); Serial.println(current_match_size);
    #endif

    for (size_t ind=0; ind<current_match_size; ind++){
        arr_to_match[ind] = to_match[ind];
    }

    reset_match_index();
}

void ExpressionMatcher::reset_match_index(void){
    current_match_index = 0;
}

bool ExpressionMatcher::match(char crrt_char){
    #if EXPRESSION_MATCHER_DEBUG
        Serial.print(F("D current_match_index: ")); Serial.println(current_match_index);
    #endif

    // if the current char is a match, need to check if a full match has been performed
    if (crrt_char == arr_to_match[current_match_index]){
        current_match_index += 1;

        // was this the last character to match?
        if (current_match_index == current_match_size){
            reset_match_index();
            return true;
        }
        else{
            return false;
        }
    }
    // if the current char is not a match, reset the matcher and return false
    else{
        reset_match_index();
        return false;
    }
}
